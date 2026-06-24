export interface Agent {
  id: string;
  icon: string;
  name: string;
  role: string;
  mock: string;
}

export const AGENTS: Agent[] = [
  {
    id: "cfo",
    icon: "💰",
    name: "CFO",
    role: "Financial",
    mock: "Financial projections show potential $50M market cap by year 3. Target burn rate of $200K/month for the first 18 months, with a death valley crossing at month 14. Recommend a Series A raise of $3M at a $15M pre-money valuation after hitting 1,000 paying customers. Unit economics need to reach CAC payback under 12 months.",
  },
  {
    id: "cmo",
    icon: "📣",
    name: "CMO",
    role: "Marketing",
    mock: "Go-to-market strategy should focus on product-led growth targeting SMBs first. Organic content + community can drive early traction. Target CAC below $150 with an LTV:CAC ratio of 4:1. Channel mix: 40% organic, 35% paid search, 25% partnerships. Launch on ProductHunt + targeted LinkedIn outreach to 500 ICP accounts.",
  },
  {
    id: "market",
    icon: "📊",
    name: "Market Analyst",
    role: "Research",
    mock: "TAM estimated at $12B globally with a SAM of $800M for the English-speaking B2B segment. Key competitors are fragmented, leaving a clear opening for a well-executed vertical play. Market growing at 24% CAGR. Top 3 competitors have NPS below 30 — customer satisfaction gap is the main wedge.",
  },
  {
    id: "vc",
    icon: "🏦",
    name: "VC Investor",
    role: "Investment",
    mock: "Strong founder-market fit potential. Seed milestones: working MVP, 10 design partners, $10K MRR. Series A trigger: $100K MRR with net revenue retention above 110%. Exit scenarios include strategic acquisition at 5–8x revenue or IPO at $300M+ ARR. Comparable exits in this space averaged 7.2x revenue.",
  },
  {
    id: "devil",
    icon: "⚠️",
    name: "Devil's Advocate",
    role: "Risk",
    mock: "Critical risks: regulatory headwinds in the EU could delay expansion 12–18 months. CAC may spike as incumbents respond aggressively. Technology moat is thin — a well-funded competitor could replicate core features in 6 months. Default scenario: if growth stalls below plan at month 18, runway collapses without bridge round.",
  },
  {
    id: "pm",
    icon: "🚀",
    name: "Product Manager",
    role: "Roadmap",
    mock: "MVP scope: core value prop in 3 user flows, shipped in 8 weeks. Phase 1 KPIs: 10-minute time-to-value, 60% D7 retention. Prioritize Slack and Google Workspace integrations for distribution leverage. V1.1 adds team collaboration features based on design partner feedback. Technical debt budget: max 20% of each sprint.",
  },
];
