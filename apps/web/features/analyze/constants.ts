export type Status = "waiting" | "thinking" | "done";

export const STATUS_STYLES: Record<Status, string> = {
  waiting: "bg-zinc-800 text-zinc-400",
  thinking: "bg-amber-900/40 text-amber-400",
  done: "bg-green-900/40 text-green-400",
};

export const STATUS_LABEL: Record<Status, string> = {
  waiting: "Waiting",
  thinking: "Thinking…",
  done: "Done",
};
