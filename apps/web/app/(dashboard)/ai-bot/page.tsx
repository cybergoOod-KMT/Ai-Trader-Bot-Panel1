import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AiBotView } from "@/components/ai-bot-view";

export default async function AiBotPage() {
  const store = await cookies();
  if (!store.get("tabdeal_panel_session")?.value) redirect("/login");
  return <AiBotView />;
}
