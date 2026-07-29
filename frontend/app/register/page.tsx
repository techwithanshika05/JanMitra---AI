"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    full_name: "", address: "", gender: "", pincode: "", mobile: "", password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const update = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async () => {
    if (!form.full_name || !form.address || !form.pincode || !form.mobile || !form.password) {
      setError("Full name, address, pincode, mobile, and password are required.");
      return;
    }
    if (form.mobile.length !== 10 || !/^\d{10}$/.test(form.mobile)) {
      setError("Mobile number must be exactly 10 digits.");
      return;
    }
    if (form.pincode.length !== 6 || !/^\d{6}$/.test(form.pincode)) {
      setError("Pincode must be exactly 6 digits.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await api.register({
        full_name: form.full_name,
        address: form.address,
        gender: form.gender || undefined,
        pincode: form.pincode,
        mobile: form.mobile,
        password: form.password,
      });
      window.localStorage.setItem("janmitra_token", res.access_token);
      window.dispatchEvent(new Event("janmitra-auth-changed"));
      router.push("/dashboard");
    } catch (e: any) {
      setError(e.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-lg mx-auto px-5 py-16">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="glass-card rounded-card p-8 shadow-card"
      >
        <h1 className="font-display text-2xl font-bold text-maroon-dark text-center">Create your account</h1>
        <p className="text-sm text-maroon-dark/60 text-center mt-1">
          You'll get a unique ID (like PDS482913) to track your applications.
        </p>

        <div className="grid md:grid-cols-2 gap-4 mt-7">
          <Field label="Full Name" required full>
            <input className="input" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} />
          </Field>
          <Field label="Mobile Number" required>
            <input
              className="input"
              maxLength={10}
              placeholder="10-digit mobile number"
              value={form.mobile}
              onChange={(e) => update("mobile", e.target.value.replace(/\D/g, ""))}
            />
          </Field>
          <Field label="Password" required>
            <input type="password" className="input" value={form.password} onChange={(e) => update("password", e.target.value)} />
          </Field>
          <Field label="Gender">
            <select className="input" value={form.gender} onChange={(e) => update("gender", e.target.value)}>
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </Field>
          <Field label="Pincode" required>
            <input
              className="input"
              maxLength={6}
              placeholder="6-digit pincode"
              value={form.pincode}
              onChange={(e) => update("pincode", e.target.value.replace(/\D/g, ""))}
            />
          </Field>
          <Field label="Address" required full>
            <textarea
              className="input min-h-[80px]"
              value={form.address}
              onChange={(e) => update("address", e.target.value)}
            />
          </Field>
        </div>

        {error && <p className="text-sm text-red-600 mt-4">{error}</p>}

        <button
          onClick={submit}
          disabled={loading}
          className="btn-primary w-full mt-6 py-3 flex items-center justify-center gap-2 disabled:opacity-60"
        >
          {loading && <Loader2 size={16} className="animate-spin" />}
          Create account
        </button>

        <p className="text-sm text-center text-maroon-dark/60 mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-rose font-semibold hover:underline">
            Log in
          </Link>
        </p>
      </motion.div>

      <style jsx global>{`
        .input {
          @apply w-full border border-blush/60 rounded-lg px-3 py-2 text-sm bg-transparent outline-none focus-visible:border-rose;
        }
      `}</style>
    </div>
  );
}

function Field({ label, children, required, full }: { label: string; children: React.ReactNode; required?: boolean; full?: boolean }) {
  return (
    <label className={`text-sm ${full ? "md:col-span-2" : ""}`}>
      <span className="block mb-1 text-maroon-dark/70">
        {label} {required && <span className="text-rose">*</span>}
      </span>
      {children}
    </label>
  );
}
