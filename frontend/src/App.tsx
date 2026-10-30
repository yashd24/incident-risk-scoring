import { useEffect, useState } from "react";
import Nav, { parseRoute } from "./components/Nav";
import NewCasePage from "./pages/NewCasePage";
import CasesPage from "./pages/CasesPage";
import CaseDetailPage from "./pages/CaseDetailPage";

export default function App() {
  const [route, setRoute] = useState(() => parseRoute(window.location.hash));

  useEffect(() => {
    const onHash = () => setRoute(parseRoute(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return (
    <main className="container">
      <Nav route={route} />
      {route.page === "new" && <NewCasePage />}
      {route.page === "cases" && <CasesPage />}
      {route.page === "case" && <CaseDetailPage key={route.id} id={route.id} />}
    </main>
  );
}
