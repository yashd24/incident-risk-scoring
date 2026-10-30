def new_case(client, name="Case A", alert_ids=(8,)):
    r = client.post("/api/cases", json={"name": name, "alert_ids": list(alert_ids)})
    assert r.status_code == 201
    return r.json()["id"]


def add(client, case_id, alert_id):
    return client.post(f"/api/cases/{case_id}/alerts", json={"alert_id": alert_id})


def test_seed_alerts(client):
    alerts = client.get("/api/alerts").json()
    assert [a["id"] for a in alerts] == list(range(1, 9))
    assert alerts[2]["base_score"] == 40


def test_duplicate_add_409(client):
    cid = new_case(client)
    assert add(client, cid, 1).status_code == 201
    r = add(client, cid, 1)
    assert r.status_code == 409
    assert "already" in r.json()["detail"]


def test_add_unknown_alert_or_case_404(client):
    cid = new_case(client)
    assert add(client, cid, 999).status_code == 404
    assert add(client, 999, 1).status_code == 404


def test_two_escalations_400(client):
    cid = new_case(client)
    r = client.put(
        f"/api/cases/{cid}/policies",
        json={"policies": ["CRITICAL_ASSET_BOOST", "APT_CAMPAIGN_LINK"]},
    )
    assert r.status_code == 400


def test_unknown_policy_422(client):
    cid = new_case(client)
    r = client.put(f"/api/cases/{cid}/policies", json={"policies": ["NOPE"]})
    assert r.status_code == 422


def test_policies_404(client):
    assert client.put("/api/cases/999/policies", json={"policies": []}).status_code == 404


def test_duplicate_policy_names_collapse(client):
    cid = new_case(client)
    r = client.put(
        f"/api/cases/{cid}/policies",
        json={"policies": ["REPEAT_NOISE_DAMPING", "REPEAT_NOISE_DAMPING"]},
    )
    assert r.json()["policies"] == ["REPEAT_NOISE_DAMPING"]


def test_blank_name_422(client):
    # alert_ids is valid so the 422 can only come from the name
    for name in ("", "   ", "x" * 101):
        assert client.post("/api/cases", json={"name": name, "alert_ids": [1]}).status_code == 422
    cid = new_case(client)
    assert client.patch(f"/api/cases/{cid}", json={"name": "  "}).status_code == 422
    assert client.get("/api/cases").json()[0]["name"] == "Case A"


def test_name_length_limit_applies_after_trimming(client):
    r = client.post("/api/cases", json={"name": f"  {'x' * 100}  ", "alert_ids": [1]})
    assert r.status_code == 201 and r.json()["name"] == "x" * 100
    r = client.patch(f"/api/cases/{r.json()['id']}", json={"name": "  Renamed  "})
    assert r.json()["name"] == "Renamed"


def test_name_trimmed_and_not_unique(client):
    a = client.post("/api/cases", json={"name": "  Dup  ", "alert_ids": [1]}).json()
    b = client.post("/api/cases", json={"name": "Dup", "alert_ids": [1]}).json()
    assert a["name"] == b["name"] == "Dup"
    assert a["id"] != b["id"]


def test_same_alert_in_two_cases(client):
    c1, c2 = new_case(client, "one"), new_case(client, "two")
    assert add(client, c1, 3).status_code == 201
    assert add(client, c2, 3).status_code == 201


def test_rename(client):
    cid = new_case(client)
    r = client.patch(f"/api/cases/{cid}", json={"name": "Renamed"})
    assert r.status_code == 200 and r.json()["name"] == "Renamed"
    assert client.patch("/api/cases/999", json={"name": "x"}).status_code == 404


def test_cascade_delete(client):
    cid = new_case(client)
    add(client, cid, 1)
    client.put(f"/api/cases/{cid}/policies", json={"policies": ["REPEAT_NOISE_DAMPING"]})
    assert client.delete(f"/api/cases/{cid}").status_code == 204
    assert client.get(f"/api/cases/{cid}").status_code == 404
    assert client.delete(f"/api/cases/{cid}").status_code == 404
    assert len(client.get("/api/alerts").json()) == 8  # alerts untouched


def test_summary_and_list(client):
    cid = new_case(client)
    for a in (3, 8):
        add(client, cid, a)
    client.put(f"/api/cases/{cid}/policies", json={"policies": ["APT_CAMPAIGN_LINK"]})
    s = client.get(f"/api/cases/{cid}/summary").json()
    assert s["raw_score"] == 65 and s["final_score"] == 90 and s["severity"] == "Critical"
    (item,) = client.get("/api/cases").json()
    assert item["alert_count"] == 2 and item["final_score"] == 90
    assert client.get("/api/cases/999/summary").status_code == 404


def test_policy_stays_requested_when_it_stops_qualifying(client):
    cid = new_case(client, alert_ids=[1])
    add(client, cid, 2)
    client.put(f"/api/cases/{cid}/policies", json={"policies": ["APT_CAMPAIGN_LINK"]})
    s = client.get(f"/api/cases/{cid}/summary").json()
    assert s["adjustments"][0]["applied"] is True and s["final_score"] == 75

    assert client.delete(f"/api/cases/{cid}/alerts/2").status_code == 204
    assert client.delete(f"/api/cases/{cid}/alerts/2").status_code == 404
    s = client.get(f"/api/cases/{cid}/summary").json()
    assert s["adjustments"][0]["applied"] is False
    assert s["final_score"] == 18
    assert client.get(f"/api/cases/{cid}").json()["policies"] == ["APT_CAMPAIGN_LINK"]

    add(client, cid, 2)  # qualifies again
    assert client.get(f"/api/cases/{cid}/summary").json()["adjustments"][0]["applied"] is True


def test_create_case_with_alerts_and_policies(client):
    r = client.post(
        "/api/cases",
        json={"name": "Full", "alert_ids": [3, 8, 3], "policies": ["APT_CAMPAIGN_LINK"]},
    )
    assert r.status_code == 201
    body = r.json()
    assert sorted(a["id"] for a in body["alerts"]) == [3, 8]
    assert body["policies"] == ["APT_CAMPAIGN_LINK"]
    s = client.get(f"/api/cases/{body['id']}/summary").json()
    assert s["final_score"] == 90


def test_create_case_rejects_bad_input_atomically(client):
    assert client.post("/api/cases", json={"name": "x", "alert_ids": [999]}).status_code == 404
    two = ["CRITICAL_ASSET_BOOST", "APT_CAMPAIGN_LINK"]
    assert client.post("/api/cases", json={"name": "x", "policies": two}).status_code == 400
    assert client.get("/api/cases").json() == []


def test_preview_summary(client):
    r = client.post(
        "/api/summary/preview", json={"alert_ids": [1, 5, 6, 7], "policies": ["REPEAT_NOISE_DAMPING"]}
    )
    assert r.status_code == 200
    assert r.json()["final_score"] == 40
    assert client.get("/api/cases").json() == []


def test_update_case_replaces_alerts_and_policies(client):
    cid = new_case(client)
    add(client, cid, 1)
    add(client, cid, 5)
    client.put(f"/api/cases/{cid}/policies", json={"policies": ["REPEAT_NOISE_DAMPING"]})
    r = client.put(
        f"/api/cases/{cid}",
        json={"alert_ids": [5, 3, 8], "policies": ["APT_CAMPAIGN_LINK"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert [a["id"] for a in body["alerts"]] == [3, 5, 8]
    assert body["policies"] == ["APT_CAMPAIGN_LINK"]
    assert client.get(f"/api/cases/{cid}/summary").json()["final_score"] == 100


def test_update_case_validation_leaves_case_untouched(client):
    cid = new_case(client, alert_ids=[1])
    assert client.put("/api/cases/999", json={"alert_ids": [], "policies": []}).status_code == 404
    assert client.put(f"/api/cases/{cid}", json={"alert_ids": [999], "policies": []}).status_code == 404
    two = ["CRITICAL_ASSET_BOOST", "APT_CAMPAIGN_LINK"]
    assert client.put(f"/api/cases/{cid}", json={"alert_ids": [], "policies": two}).status_code == 400
    assert client.put(f"/api/cases/{cid}", json={"alert_ids": [], "policies": ["NOPE"]}).status_code == 422
    assert client.put(f"/api/cases/{cid}", json={}).status_code == 422  # both fields are required
    assert [a["id"] for a in client.get(f"/api/cases/{cid}").json()["alerts"]] == [1]


def test_update_case_cannot_empty_the_case(client):
    cid = new_case(client, alert_ids=[1])
    r = client.put(f"/api/cases/{cid}", json={"alert_ids": [], "policies": []})
    assert r.status_code == 422
    assert r.json()["detail"] == "A case needs at least one alert"
    assert [a["id"] for a in client.get(f"/api/cases/{cid}").json()["alerts"]] == [1]


def test_cannot_remove_the_last_alert(client):
    cid = new_case(client, alert_ids=[1])
    r = client.delete(f"/api/cases/{cid}/alerts/1")
    assert r.status_code == 422
    assert r.json()["detail"] == "A case needs at least one alert"
    assert add(client, cid, 2).status_code == 201
    assert client.delete(f"/api/cases/{cid}/alerts/1").status_code == 204
    assert client.delete(f"/api/cases/{cid}/alerts/2").status_code == 422


def test_create_case_requires_at_least_one_alert(client):
    for body in (
        {"name": "Empty"},
        {"name": "Empty", "alert_ids": []},
        {"name": "Empty", "alert_ids": [], "policies": ["REPEAT_NOISE_DAMPING"]},
    ):
        r = client.post("/api/cases", json=body)
        assert r.status_code == 422
        assert r.json()["detail"] == "A case needs at least one alert"
    assert client.get("/api/cases").json() == []
