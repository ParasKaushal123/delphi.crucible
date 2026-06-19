"use client";
import { useEffect, useRef } from "react";

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let time = 0;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", resize);
    resize();

    // Define some orbital paths using the Mesh colors
    // #fefef7 (Bone White) and #f2b98b (Bronze Glow)
    const orbits = [
      { radiusX: 0.6, radiusY: 0.2, speed: 0.0005, color: "rgba(254, 254, 247, 0.4)", cx: 0.3, cy: 0.7, rotation: 0.2, lineWidth: 1.5, blur: 4 },
      { radiusX: 0.8, radiusY: 0.4, speed: -0.0003, color: "rgba(242, 185, 139, 0.3)", cx: 0.8, cy: 0.2, rotation: -0.3, lineWidth: 2, blur: 8 },
      { radiusX: 0.7, radiusY: 0.3, speed: 0.0002, color: "rgba(254, 254, 247, 0.15)", cx: 0.5, cy: 0.5, rotation: 0.5, lineWidth: 1, blur: 2 },
      { radiusX: 0.9, radiusY: 0.5, speed: -0.0004, color: "rgba(242, 185, 139, 0.2)", cx: 0.2, cy: 0.2, rotation: -0.1, lineWidth: 3, blur: 15 },
      { radiusX: 0.5, radiusY: 0.25, speed: 0.0006, color: "rgba(254, 254, 247, 0.3)", cx: 0.8, cy: 0.8, rotation: 0.8, lineWidth: 1.5, blur: 5 },
      { radiusX: 1.2, radiusY: 0.6, speed: 0.0001, color: "rgba(242, 185, 139, 0.15)", cx: 0.5, cy: 0.5, rotation: 0, lineWidth: 4, blur: 20 },
    ];

    const draw = () => {
      time += 16;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const w = canvas.width;
      const h = canvas.height;
      const size = Math.max(w, h);

      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      orbits.forEach((orbit) => {
        ctx.beginPath();
        const centerX = w * orbit.cx;
        const centerY = h * orbit.cy;
        const rX = size * orbit.radiusX;
        const rY = size * orbit.radiusY;

        for (let angle = 0; angle < Math.PI * 2; angle += 0.05) {
          // Calculate ellipse point
          const x = Math.cos(angle) * rX;
          const y = Math.sin(angle) * rY;
          
          // Apply rotation
          const rotX = x * Math.cos(orbit.rotation) - y * Math.sin(orbit.rotation);
          const rotY = x * Math.sin(orbit.rotation) + y * Math.cos(orbit.rotation);

          // Add wave distortion based on time
          const wave = Math.sin(angle * 4 + time * orbit.speed) * (size * 0.015);
          const finalX = centerX + rotX + Math.cos(angle) * wave;
          const finalY = centerY + rotY + Math.sin(angle) * wave;
          
          if (angle === 0) {
            ctx.moveTo(finalX, finalY);
          } else {
            ctx.lineTo(finalX, finalY);
          }
        }
        ctx.closePath();
        
        ctx.lineWidth = orbit.lineWidth;
        ctx.strokeStyle = orbit.color;
        ctx.shadowBlur = orbit.blur;
        ctx.shadowColor = orbit.color.replace(/[^,]+(?=\))/, '1'); 
        ctx.stroke();

        // Draw glowing particle
        const pAngle = (time * orbit.speed * 2) % (Math.PI * 2);
        const px = Math.cos(pAngle) * rX;
        const py = Math.sin(pAngle) * rY;
        const protX = px * Math.cos(orbit.rotation) - py * Math.sin(orbit.rotation);
        const protY = px * Math.sin(orbit.rotation) + py * Math.cos(orbit.rotation);
        const pWave = Math.sin(pAngle * 4 + time * orbit.speed) * (size * 0.015);
        const finalPx = centerX + protX + Math.cos(pAngle) * pWave;
        const finalPy = centerY + protY + Math.sin(pAngle) * pWave;
        
        ctx.beginPath();
        ctx.arc(finalPx, finalPy, orbit.lineWidth * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = orbit.color.replace(/[^,]+(?=\))/, '1'); 
        ctx.shadowBlur = orbit.blur * 2 + 10;
        ctx.fill();
        
        // Occasional smaller particle
        const pAngle2 = (time * orbit.speed * 1.5 + Math.PI) % (Math.PI * 2);
        const px2 = Math.cos(pAngle2) * rX;
        const py2 = Math.sin(pAngle2) * rY;
        const protX2 = px2 * Math.cos(orbit.rotation) - py2 * Math.sin(orbit.rotation);
        const protY2 = px2 * Math.sin(orbit.rotation) + py2 * Math.cos(orbit.rotation);
        const pWave2 = Math.sin(pAngle2 * 4 + time * orbit.speed) * (size * 0.015);
        const finalPx2 = centerX + protX2 + Math.cos(pAngle2) * pWave2;
        const finalPy2 = centerY + protY2 + Math.sin(pAngle2) * pWave2;

        ctx.beginPath();
        ctx.arc(finalPx2, finalPy2, orbit.lineWidth * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = orbit.color.replace(/[^,]+(?=\))/, '0.8'); 
        ctx.shadowBlur = orbit.blur + 5;
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="fixed inset-0 z-[-1] overflow-hidden bg-[#0f0f10] pointer-events-none">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(26,26,28,0.8)_0%,rgba(15,15,16,1)_100%)]"></div>
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-70"></canvas>
      <div 
        className="absolute inset-0 opacity-[0.04] mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`
        }}
      ></div>
      {/* Warm amber glow at the bottom as specified in frontenddesign.md */}
      <div className="absolute bottom-0 left-0 right-0 h-[60vh] bg-gradient-to-t from-[rgba(212,144,101,0.4)] to-transparent pointer-events-none mix-blend-screen"></div>
    </div>
  );
}
