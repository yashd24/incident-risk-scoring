# Prompts

The planning discussion prompts (D1–D10), then the build prompts (1–10), listed in the order they were given, with their original wording. Some small follow-up tweaks ("build FE", font size, tab label, "list them") are left out.

## Planning discussion
These prompts produced the build plan (its decisions log covers stack, case/alert semantics, policy order and rounding, requested-vs-applied behaviour, API and UI shape, and tests).

### D1
> we have to build this, first discussion, then planning, then execution. do not assume anything ask questions.

### D2
> in frontend we will use react, for backend fast api.

### D3
> boost will be applied after damping

### D4
> floor the final score. is there any cases in this situation?

### D5
> option 1, but what if the user wants to remove it? it shows not applied with a reason, and the user adds another alert in that, and it again become active?

### D6
> we will have multiple cases. no auth required. first give me a list of questions that you got answers to and which are pending to answer

### D7
> use type script. and alembic migrations

### D8
> Are all the decisions final? Verify everything. Do not assume. Ask questions for clarity. If yes give me a plan.md. If not, tell me which are open questions.

### D9
> it will come from backend.. a flag.

### D10
> tie rule pick the latest one. cases will be compared using the id. unique identifier will be id always throughout the codebase

## 1. Build the plan
> execute this plan... list the open questions in the end. do not commit anything.

(followed by the full contents of the build plan)

## 2. Create a case from a draft, and add a cases list page
> add the submit button, i'll add the alerts in the case select the policies, then i'll click create case then it will create the case. also one page where all the cases are listed

## 3. Bump the frontend image and smoke-test the UI
Reply to the open question (bump the Docker image to Node 22, and smoke-test the UI against the backend):

> open question - yes

## 4. Run the full Docker stack
> docker daemon is running and reachable

## 5. Where the create button and name go, and how the UI should be styled
> still there is no submit button for the cases. also improve the UI. Ask questions do not assume anything

Answers given to the clarifying questions:

> i'll select the alerts, select the policies. then below the final score, it should show create case button. name should also be entered there which should be a required field.

> it should look good + minimal changes. for example - hand written css will bring a lot of changes(in my opinion)

## 6. Case page header: smaller buttons next to the case name
(sent with a screenshot of the case page header)

> the buttons are big... the case name should be identifiable. and in front of it the buttons should be there.

## 7. Separate the nav from the case header, drop the page title
(sent with a screenshot of the nav and case header)

> no segregation here makes it look clustered.
> remove the Case Risk Scoring.

## 8. Edit an existing case with a single Update call
(sent with a screenshot of the case page)

> in this i should be able to update the policies, and then update button which fires the api and updates the case. API should be fired once at last.

Answers given to the clarifying questions:

> rename - i enter the new name -> then i click okay (or a tick icon) then api call -> name updtes.
> policies and alerts - i modify policies and alerts -> i click on update (same position like i click on create case) -> case updates

## 9. Backend validation for creating a case
> Add validation for create case... it should not create if no alerts are passed. Backend api validation.
> Rename - if the name is same then no api call.

## 10. Extend the validation to the other endpoints and the UI
Reply to the follow-up questions (1: also require at least one alert on update; 2: disable the button and keep the server message):

> 1. yes
> 2. both
>
> backend validation should be present in neccessary apis
