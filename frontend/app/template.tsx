"use client";

import { motion } from "framer-motion";

const variants = {
  hidden: { opacity: 0, x: 0, y: 20 },
  enter: { opacity: 1, x: 0, y: 0 },
};

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.main
      variants={variants}
      initial="hidden"
      animate="enter"
      transition={{ type: "spring", stiffness: 100, damping: 20, duration: 0.4 }}
      className="w-full min-h-screen"
    >
      {children}
    </motion.main>
  );
}
