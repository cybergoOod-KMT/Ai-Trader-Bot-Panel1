import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { StrategyBotsView } from "@/components/strategy-bots-view";

export default async function StrategyBotsPage() {
  const store = await cookies();
  if (!store.get("tabdeal_panel_session")?.value) redirect("/login");
  return <StrategyBotsView />;
}
