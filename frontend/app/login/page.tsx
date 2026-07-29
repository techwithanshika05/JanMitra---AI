"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { User, ShieldCheck, UserRound, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useLanguage } from "@/lib/i18n";

type Role = "user" | "admin" | "guest";

export default function LoginPage() {
  const router = useRouter();
  const { lang } = useLanguage();
  const hi = lang === "hi";
  const [role, setRole] = useState<Role>("user");
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const continueAsGuest = () => {
    window.localStorage.removeItem("janmitra_token");
    router.push("/dashboard");
  };

  const submit = async () => {
    if (!mobile || !password) {
      setError(hi ? "कृपया मोबाइल नंबर और पासवर्ड दोनों दर्ज करें।" : "Please enter both mobile number and password.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await api.login({ mobile, password });
      if (role === "admin" && res.user.role !== "admin") {
        setError(hi ? "इस खाते में एडमिन पहुंच नहीं है।" : "This account does not have admin access.");
        setLoading(false);
        return;
      }
      window.localStorage.setItem("janmitra_token", res.access_token);
      router.push(role === "admin" ? "/admin" : "/dashboard");
    } catch (e: any) {
      setError(e.message || (hi ? "लॉगिन विफल रहा। अपना मोबाइल नंबर और पासवर्ड जांचें।" : "Login failed. Check your mobile number and password."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-5 py-16">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="glass-card rounded-card p-8 shadow-card"
      >
        <h1 className="font-display text-2xl font-bold text-maroon-dark text-center">{hi ? "वापसी पर स्वागत है" : "Welcome back"}</h1>
        <p className="text-sm text-maroon-dark/60 text-center mt-1">{hi ? "आप कैसे जारी रखना चाहेंगे, चुनें" : "Choose how you'd like to continue"}</p>

        <div className="grid grid-cols-3 gap-2 mt-6">
          {[
            { key: "user" as Role, label: hi ? "उपयोगकर्ता" : "User", icon: User },
            { key: "admin" as Role, label: hi ? "एडमिन" : "Admin", icon: ShieldCheck },
            { key: "guest" as Role, label: hi ? "अतिथि" : "Guest", icon: UserRound },
          ].map((r) => {
            const Icon = r.icon;
            const active = role === r.key;
            return (
              <button
                key={r.key}
                onClick={() => setRole(r.key)}
                className={`flex flex-col items-center gap-1.5 py-3 rounded-lg border-2 transition-colors text-xs font-semibold ${
                  active ? "border-rose bg-blush/40 text-maroon-dark" : "border-blush/60 text-maroon-dark/50 hover:border-rose/50"
                }`}
              >
                <Icon size={18} />
                {r.label}
              </button>
            );
          })}
        </div>

        {role === "guest" ? (
          <div className="mt-7">
            <p className="text-sm text-maroon-dark/60 text-center">
              {hi
                ? "बिना खाते के योजनाएं देखें, चैट करें, और चेकलिस्ट बनाएं। कुछ सुविधाओं (जैसे सेव इतिहास) के लिए पूर्ण खाता चाहिए।"
                : "Browse schemes, chat, and generate checklists without an account. Some features (like saved history) need a full account."}
            </p>
            <button
              onClick={continueAsGuest}
              className="btn-primary w-full mt-5 py-3 flex items-center justify-center gap-2"
            >
              {hi ? "अतिथि के रूप में जारी रखें" : "Continue as Guest"}
            </button>
          </div>
        ) : (
          <div className="mt-7 space-y-4">
            <div>
              <label className="text-sm font-medium text-maroon-dark">{hi ? "मोबाइल नंबर" : "Mobile Number"}</label>
              <input
                type="tel"
                maxLength={10}
                value={mobile}
                onChange={(e) => setMobile(e.target.value.replace(/\D/g, ""))}
                placeholder={role === "admin" ? "9999999999" : (hi ? "10-अंकों का मोबाइल नंबर" : "10-digit mobile number")}
                className="w-full mt-1 border border-blush/60 rounded-lg px-3 py-2 text-sm outline-none focus-visible:border-rose"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-maroon-dark">{hi ? "पासवर्ड" : "Password"}</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
                placeholder="••••••••"
                className="w-full mt-1 border border-blush/60 rounded-lg px-3 py-2 text-sm outline-none focus-visible:border-rose"
              />
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              onClick={submit}
              disabled={loading}
              className="btn-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading && <Loader2 size={16} className="animate-spin" />}
              {hi
                ? `${role === "admin" ? "एडमिन" : "उपयोगकर्ता"} के रूप में लॉगिन करें`
                : `Log in as ${role === "admin" ? "Admin" : "User"}`}
            </button>

            {role === "user" && (
              <p className="text-sm text-center text-maroon-dark/60">
                {hi ? "नए हैं? " : "New here? "}
                <Link href="/register" className="text-rose font-semibold hover:underline">
                  {hi ? "खाता बनाएं" : "Create an account"}
                </Link>
              </p>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}
