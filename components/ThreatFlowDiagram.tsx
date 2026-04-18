"use client";

import React, { useEffect, useRef } from "react";
import * as d3 from "d3";

const ThreatFlowDiagram = () => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 800;
    const height = 400;
    const svg = d3.select(svgRef.current)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .style("overflow", "visible");

    svg.selectAll("*").remove();

    const data = {
      nodes: [
        { id: "User Email", x: 100, y: 200, color: "#a855f7" },
        { id: "AI Detection", x: 300, y: 200, color: "#00ffff" },
        { id: "Classification", x: 500, y: 200, color: "#10b981" },
        { id: "Dashboard Report", x: 700, y: 200, color: "#f59e0b" },
      ],
      links: [
        { source: 0, target: 1 },
        { source: 1, target: 2 },
        { source: 2, target: 3 },
      ]
    };

    // Draw links
    svg.selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("x1", d => data.nodes[d.source]!.x)
      .attr("y1", d => data.nodes[d.source]!.y)
      .attr("x2", d => data.nodes[d.target]!.x)
      .attr("y2", d => data.nodes[d.target]!.y)
      .attr("stroke", "#ffffff20")
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "5,5")
      .style("opacity", 0.5);

    // Draw nodes
    const nodes = svg.selectAll("g")
      .data(data.nodes)
      .enter()
      .append("g")
      .attr("transform", d => `translate(${d.x},${d.y})`);

    nodes.append("circle")
      .attr("r", 40)
      .attr("fill", d => d.color)
      .style("opacity", 0.2)
      .style("stroke", d => d.color)
      .style("stroke-width", 2);

    nodes.append("circle")
      .attr("r", 8)
      .attr("fill", d => d.color)
      .style("filter", "blur(2px)");

    nodes.append("text")
      .text(d => d.id)
      .attr("y", 60)
      .attr("text-anchor", "middle")
      .attr("fill", "#ffffff50")
      .style("font-size", "12px")
      .style("font-weight", "bold")
      .style("text-transform", "uppercase")
      .style("letter-spacing", "2px");

    // Add animated particles along lines
    svg.selectAll(".particle")
      .data(data.links)
      .enter()
      .append("circle")
      .attr("r", 3)
      .attr("fill", "#00ffff")
      .attr("filter", "blur(2px)")
      .each(function(d) {
        const line = this;
        const start = data.nodes[d.source]!;
        const end = data.nodes[d.target]!;
        
        function animate() {
          d3.select(line)
            .attr("cx", start.x)
            .attr("cy", start.y)
            .style("opacity", 1)
            .transition()
            .duration(2000 + Math.random() * 1000)
            .ease(d3.easeLinear)
            .attr("cx", end.x)
            .attr("cy", end.y)
            .on("end", animate);
        }
        animate();
      });

  }, []);

  return (
    <div className="w-full h-full flex items-center justify-center p-8 bg-white/5 rounded-[40px] border border-white/5 overflow-hidden">
      <svg ref={svgRef} className="w-full max-w-4xl h-auto" />
    </div>
  );
};

export default ThreatFlowDiagram;
