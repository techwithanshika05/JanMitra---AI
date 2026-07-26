"use client";
import { motion } from "framer-motion";

export default function StatCard({ value, label, index = 0 }: { value: string; label: string; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="glass-card rounded-card px-6 py-8 text-center"
    >
      <p className="font-display text-4xl font-extrabold bg-gradient-primary bg-clip-text text-transparent">
        {value}
      </p>
      <p className="text-sm text-maroon-dark/60 mt-2 font-medium">{label}</p>
    </motion.div>
  );
}
