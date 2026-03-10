"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [data, setData] = useState<{ message: string } | null>(null);

  useEffect(() => {
    async function testConnection() {
      const url = "http://localhost:8000/";
      const res = await fetch(url);
      const result = await res.json();
      setData(result);
    }
    testConnection();
  }, []);
  return (
    <div>
      <p>{data?.message}</p>
    </div>
  );
}
