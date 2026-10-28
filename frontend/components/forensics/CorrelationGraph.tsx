"use client";

/**
 * CorrelationGraph — genuinely data-driven interactive relationship graph.
 * Nodes and edges come exclusively from the backend analysis result
 * (result.graph.nodes / result.graph.edges), built from observable evidence.
 * Empty graph → explicit "no data" message; never decorative.
 */
import React, { useEffect, useRef, useState, useMemo } from "react";
import * as d3 from "d3";
import { Network, MousePointerClick } from "lucide-react";

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  [key: string]: any;
}
export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  evidence: string;
  confidence: number;
}

export const TYPE_COLORS: Record<string, string> = {
  email: "#22d3ee",
  sender: "#a78bfa",
  domain: "#34d399",
  ip: "#f472b6",
  mail_server: "#fbbf24",
  nameserver: "#fbbf24",
  url: "#60a5fa",
  asn: "#fb7185",
  organization: "#94a3b8",
  campaign: "#e879f9",
  previous_incident: "#fb923c",
  attachment: "#4ade80",
  unavailable: "#64748b",
};

export default function CorrelationGraph({ graph }: { graph?: { nodes: GraphNode[]; edges: GraphEdge[]; summary?: any } | null | undefined }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  const nodes = useMemo(() => graph?.nodes ?? [], [graph]);
  const edges = useMemo(() => graph?.edges ?? [], [graph]);
  const nodeTypes = useMemo(() => Array.from(new Set(nodes.map((n) => n.type))).sort(), [nodes]);

  const visibleNodes = useMemo(
    () => (typeFilter ? nodes.filter((n) => n.type === typeFilter) : nodes),
    [nodes, typeFilter]
  );
  const visibleIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);
  const visibleEdges = useMemo(
    () => edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [edges, visibleIds]
  );
  const neighborIds = useMemo(() => {
    if (!selected) return null;
    const s = new Set<string>([selected.id]);
    edges.forEach((e) => {
      if (e.source === selected.id) s.add(e.target);
      if (e.target === selected.id) s.add(e.source);
    });
    return s;
  }, [selected, edges]);

  useEffect(() => {
    if (!svgRef.current || visibleNodes.length === 0) return;
    const width = svgRef.current.clientWidth || 800;
    const height = 460;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const simNodes = visibleNodes.map((n) => ({ ...n }));
    const simLinks = visibleEdges.map((e) => ({ source: e.source, target: e.target, relation: e.relation }));

    const g = svg.append("g");
    const linkG = g.append("g");
    const nodeG = g.append("g");

    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.4, 3])
        .on("zoom", (event) => g.attr("transform", event.transform))
    );

    const simulation = d3
      .forceSimulation(simNodes as any)
      .force("link", d3.forceLink(simLinks as any).id((d: any) => d.id).distance(110).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-320))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(34));

    const edgeTitleMap = new Map<string, GraphEdge>(
      visibleEdges.map((e) => [`${e.source}|${e.target}`, e])
    );

    const link = linkG
      .selectAll("line")
      .data(simLinks)
      .join("line")
      .attr("stroke", "#475569")
      .attr("stroke-opacity", 0.55)
      .attr("stroke-width", 1.4);

    link.append("title").text((d: any) => {
      const e = edgeTitleMap.get(`${d.source.id ?? d.source}|${d.target.id ?? d.target}`);
      return e ? `${e.relation} — ${e.evidence} (confidence ${Math.round(e.confidence * 100)}%)` : "";
    });
    const node = nodeG
      .selectAll("g")
      .data(simNodes as any)
      .join("g")
      .style("cursor", "pointer")
      .on("click", (event: any, d: any) => {
        event.stopPropagation();
        setSelected((prev) => (prev && prev.id === d.id ? null : d));
      })
      .call(
        d3
          .drag<any, any>()
          .on("start", (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event: any, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event: any, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node
      .append("circle")
      .attr("r", (d: any) => (d.type === "email" ? 22 : d.type === "previous_incident" ? 14 : 13))
      .attr("fill", (d: any) => TYPE_COLORS[d.type] || "#64748b")
      .attr("fill-opacity", 0.85)
      .attr("stroke", (d: any) => (d.origin_candidate ? "#f97316" : "#0f172a"))
      .attr("stroke-width", (d: any) => (d.origin_candidate ? 3 : 1.5));

    node
      .append("text")
      .text((d: any) => {
        const label = String(d.label ?? "");
        return label.length > 26 ? label.slice(0, 24) + "…" : label;
      })
      .attr("text-anchor", "middle")
      .attr("dy", (d: any) => (d.type === "email" ? 36 : 28))
      .attr("fill", "#cbd5e1")
      .attr("font-size", 10)
      .attr("font-family", "ui-monospace, monospace");

    node.append("title").text((d: any) => `${d.type}: ${d.label}`);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);
      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [visibleNodes, visibleEdges]);

  if (!nodes.length) {
    return (
      <div className="p-8 text-center text-white/40 text-sm bg-white/5 rounded-2xl border border-white/10 space-y-2">
        <Network className="w-8 h-8 text-white/20 mx-auto" />
        <p className="font-semibold text-white/70">No correlation data available</p>
        <p className="text-xs text-white/30">
          The graph is built exclusively from observable indicators (sender, relay IPs, DNS, RDAP,
          URLs, prior incidents). None were present in this analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-[11px]">
        {nodeTypes.map((t) => (
          <button
            key={t}
            onClick={() => setTypeFilter((prev) => (prev === t ? null : t))}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border transition-all ${
              typeFilter === t
                ? "bg-white/15 border-white/30 text-white font-bold"
                : "bg-white/5 border-white/10 text-white/60 hover:bg-white/10"
            }`}
          >
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: TYPE_COLORS[t] || "#64748b" }} />
            {t} <span className="text-white/30">({nodes.filter((n) => n.type === t).length})</span>
          </button>
        ))}
        <span className="ml-auto flex items-center gap-1.5 text-white/30">
          <MousePointerClick className="w-3.5 h-3.5" /> click to inspect · drag nodes · scroll to zoom
        </span>
      </div>

      <div className="relative w-full bg-black/40 rounded-2xl border border-white/10 overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ height: 460 }} onClick={() => setSelected(null)} />
        {selected && (
          <div className="absolute top-3 right-3 max-w-xs p-4 bg-background/95 border border-white/20 rounded-xl space-y-1.5 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: TYPE_COLORS[selected.type] || "#64748b" }} />
              <span className="font-bold text-white uppercase tracking-wider text-[10px]">{selected.type}</span>
            </div>
            <p className="font-mono text-white/90 break-all">{selected.label}</p>
            {neighborIds && <p className="text-white/40">{neighborIds.size - 1} directly connected indicator(s)</p>}
            {selected.origin_candidate && <p className="text-secondary font-semibold">Probable observable origin node</p>}
            {edges
              .filter((e) => e.source === selected.id || e.target === selected.id)
              .slice(0, 6)
              .map((e, i) => (
                <p key={i} className="text-white/50 border-t border-white/10 pt-1">
                  <span className="text-primary">{e.relation}</span> — {e.evidence}
                </p>
              ))}
          </div>
        )}
      </div>

      <p className="text-[10px] text-white/30 px-1">
        Data-driven graph: nodes are created only from observable analysis evidence (Received chain,
        DNS/RDAP, geolocation, URLs, attachments, prior cases). No decorative placeholders.
      </p>
    </div>
  );
}


