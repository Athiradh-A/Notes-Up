"use client";
import { Canvas } from "@react-three/fiber";
import { MeshDistortMaterial, Sphere, OrbitControls } from "@react-three/drei";

export default function KnowledgeOrb() {
  return (
    <div className="h-64 w-64">
      <Canvas>
        <ambientLight intensity={1} />
        <directionalLight position={[2, 5, 2]} />
        <Sphere args={[1, 100, 200]} scale={2.4}>
          <MeshDistortMaterial
            color="#A7C7E7"
            attach="material"
            distort={0.4}
            speed={2}
          />
        </Sphere>
        <OrbitControls enableZoom={false} />
      </Canvas>
    </div>
  );
}
