import { useEffect, useState } from "react";
import type { Facets } from "./api";
import { api } from "./api";
import { AppShell, Notice, type PageId } from "./components/AppShell";
import { ExerciseCatalog } from "./components/ExerciseCatalog";
import { WorkoutBuilder } from "./components/WorkoutBuilder";
import { EquipmentBrowser } from "./components/EquipmentBrowser";
import { GarminSettings } from "./components/GarminSettings";

export default function App() {
  const [page, setPage] = useState<PageId>("builder");
  // Facets carry the muscle taxonomy and the filter vocabularies. Fetched once
  // and passed down, since they never change during a session.
  const [facets, setFacets] = useState<Facets | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .facets()
      .then(setFacets)
      .catch((err: Error) => setError(`Não foi possível acessar a API: ${err.message}`));
  }, []);

  return (
    <AppShell page={page} onNavigate={setPage}>
      {error && <Notice kind="error">{error}</Notice>}
      {page === "builder" && <WorkoutBuilder facets={facets} />}
      {page === "catalog" && <ExerciseCatalog facets={facets} />}
      {page === "equipment" && <EquipmentBrowser facets={facets} />}
      {page === "settings" && <GarminSettings />}
    </AppShell>
  );
}
