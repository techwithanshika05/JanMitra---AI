"use client";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export default function FeatureCard({
  icon: Icon,
  title,
  desc,
  href,
  index = 0,
}: {
  icon: React.ElementType;
  title: string;
  desc: string;
  href: string;
  index?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.08, duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
    >
      <Link
        href={href}
        className="group premium-card gradient-border block rounded-card p-6 shadow-card bg-white h-full"
      >
        <span className="w-12 h-12 rounded-2xl bg-gradient-warm flex items-center justify-center text-white shadow-glow">
          <Icon size={20} />
        </span>
        <h3 className="font-display text-lg font-bold mt-5 text-maroon-dark">{title}</h3>
        <p className="text-sm text-maroon-dark/60 mt-2 leading-relaxed">{desc}</p>
        <span className="inline-flex items-center gap-1 text-sm font-semibold text-rose mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
          Explore <ArrowUpRight size={14} />
        </span>
      </Link>
    </motion.div>
  );
}
