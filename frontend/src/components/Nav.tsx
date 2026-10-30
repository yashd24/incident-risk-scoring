export type Route = { page: "new" } | { page: "cases" } | { page: "case"; id: number };

export function parseRoute(hash: string): Route {
  const m = hash.match(/^#\/cases\/(\d+)$/);
  if (m) return { page: "case", id: Number(m[1]) };
  if (hash === "#/cases") return { page: "cases" };
  return { page: "new" };
}

export default function Nav({ route }: { route: Route }) {
  return (
    <nav className="bar">
      <a href="#/new" className={route.page === "new" ? "active" : ""}>
        Alerts
      </a>
      <a href="#/cases" className={route.page !== "new" ? "active" : ""}>
        All cases
      </a>
    </nav>
  );
}
