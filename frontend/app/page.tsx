"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "../stores/auth";
import { dashboardsApi } from "../lib/api";
import toast from "react-hot-toast";

export default function Home() {
  const { user, isAuthenticated, isLoading, fetchUser, logout } = useAuthStore();
  const router = useRouter();
  const [dashboards, setDashboards] = useState<any[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  const [newDashName, setNewDashName] = useState("");

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboards();
    }
  }, [isAuthenticated]);

  const loadDashboards = async () => {
    setLoadingData(true);
    try {
      const res = await dashboardsApi.list();
      setDashboards(res.data);
    } catch (err: any) {
      toast.error("Failed to load dashboards");
    } finally {
      setLoadingData(false);
    }
  };

  const handleCreateDashboard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDashName.trim()) return;
    try {
      await dashboardsApi.create({ name: newDashName });
      setNewDashName("");
      toast.success("Dashboard created!");
      loadDashboards();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to create dashboard");
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated || !user) return null;

  return (
    <div className="flex min-h-screen w-full flex-col bg-gray-50">
      <header className="flex h-16 items-center justify-between border-b bg-white px-6">
        <h1 className="text-xl font-bold text-gray-900">Wexa Analytics</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-600">{user.email}</span>
          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
            {user.role}
          </span>
          <button
            onClick={handleLogout}
            className="rounded px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="flex-1 p-8">
        <div className="mx-auto max-w-5xl">
          <div className="mb-8 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">Your Dashboards</h2>
          </div>

          <div className="mb-8 rounded-lg border bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-lg font-medium text-gray-900">Create New Dashboard</h3>
            <form onSubmit={handleCreateDashboard} className="flex gap-4">
              <input
                type="text"
                placeholder="Dashboard Name (e.g. Sales Overview)"
                className="flex-1 rounded-md border py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={newDashName}
                onChange={(e) => setNewDashName(e.target.value)}
              />
              <button
                type="submit"
                className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Create
              </button>
            </form>
          </div>

          {loadingData ? (
            <p>Loading dashboards...</p>
          ) : dashboards.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-300 p-12 text-center text-gray-500">
              No dashboards yet. Create your first one above!
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {dashboards.map((dash) => (
                <div key={dash.id} className="flex flex-col justify-between rounded-lg border bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{dash.name}</h3>
                    <p className="mt-1 text-sm text-gray-500">Widgets: {dash.widget_count}</p>
                  </div>
                  <div className="mt-6 flex justify-end gap-2">
                    <button className="text-sm font-medium text-blue-600 hover:text-blue-500">
                      View
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
