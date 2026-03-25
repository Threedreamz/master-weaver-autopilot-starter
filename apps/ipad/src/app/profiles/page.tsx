"use client";

import { useEffect, useState, useCallback } from "react";
import type { ScanProfile } from "@autopilot/types";
import * as api from "@/lib/api-client";

type ProfileFormData = {
  name: string;
  magnification: "125L" | "100L" | "50L";
  voltage: string;
  ampere: string;
  rotationDegrees: string;
  description: string;
};

const emptyForm: ProfileFormData = {
  name: "",
  magnification: "125L",
  voltage: "",
  ampere: "",
  rotationDegrees: "360",
  description: "",
};

function ProfileCard({
  profile,
  isActive,
  onEdit,
  onDelete,
  onSelect,
}: {
  profile: ScanProfile;
  isActive: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onSelect: () => void;
}) {
  return (
    <div
      className={`p-4 bg-gray-900 border rounded-xl ${
        isActive ? "border-blue-500 ring-1 ring-blue-500/50" : "border-gray-800"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg truncate">{profile.name}</h3>
            {isActive && (
              <span className="flex-shrink-0 px-2 py-0.5 bg-blue-600 text-white text-xs font-bold rounded-full">
                Aktiv
              </span>
            )}
          </div>
          {profile.description && (
            <p className="text-sm text-gray-400 mt-1">{profile.description}</p>
          )}
        </div>
        <div className="flex gap-2 flex-shrink-0 ml-2">
          <button
            onClick={onEdit}
            className="min-h-[48px] min-w-[48px] flex items-center justify-center rounded-xl bg-gray-800 text-blue-400 active:bg-gray-700"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              className="w-5 h-5"
            >
              <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="min-h-[48px] min-w-[48px] flex items-center justify-center rounded-xl bg-gray-800 text-red-400 active:bg-gray-700"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              className="w-5 h-5"
            >
              <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      <div className="flex gap-4 mt-3 text-sm text-gray-400">
        <span className="px-2 py-1 bg-gray-800 rounded">
          {profile.magnification}
        </span>
        <span>{profile.voltage ?? "—"} kV</span>
        <span>{profile.ampere ?? "—"} uA</span>
        <span>{profile.rotationDegrees}&deg;</span>
      </div>

      {/* Select as active button */}
      {!isActive && (
        <button
          onClick={onSelect}
          className="mt-3 w-full min-h-[48px] bg-gray-800 border border-gray-700 text-blue-400 font-semibold rounded-xl active:bg-gray-700"
        >
          Als aktiv setzen
        </button>
      )}
    </div>
  );
}

export default function ProfilesPage() {
  const [profiles, setProfiles] = useState<ScanProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);
  const [editing, setEditing] = useState<ScanProfile | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ProfileFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<ScanProfile | null>(null);

  const loadProfiles = useCallback(() => {
    api.getProfiles().then(setProfiles).catch(() => {});
  }, []);

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setError(null);
    setShowForm(true);
  };

  const openEdit = (profile: ScanProfile) => {
    setEditing(profile);
    setForm({
      name: profile.name,
      magnification: profile.magnification,
      voltage: profile.voltage?.toString() ?? "",
      ampere: profile.ampere?.toString() ?? "",
      rotationDegrees: profile.rotationDegrees.toString(),
      description: profile.description ?? "",
    });
    setError(null);
    setShowForm(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const data = {
        name: form.name,
        magnification: form.magnification,
        voltage: form.voltage ? Number(form.voltage) : undefined,
        ampere: form.ampere ? Number(form.ampere) : undefined,
        rotationDegrees: Number(form.rotationDegrees) || 360,
        description: form.description || undefined,
      };
      if (editing) {
        await api.updateProfile(editing.id, data);
      } else {
        await api.createProfile(data);
      }
      setShowForm(false);
      loadProfiles();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Speichern fehlgeschlagen"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (profile: ScanProfile) => {
    setDeleteTarget(profile);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await api.deleteProfile(deleteTarget.id);
      if (activeProfileId === deleteTarget.id) {
        setActiveProfileId(null);
      }
      loadProfiles();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Löschen fehlgeschlagen"
      );
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleSelectActive = async (profile: ScanProfile) => {
    try {
      await api.selectProfile(profile.id);
      setActiveProfileId(profile.id);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Auswahl fehlgeschlagen"
      );
    }
  };

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Profile</h1>
        <button
          onClick={openCreate}
          className="min-h-[48px] px-6 bg-blue-600 text-white font-semibold rounded-xl active:bg-blue-700"
        >
          + Neues Profil
        </button>
      </div>

      {/* Error banner */}
      {error && !showForm && (
        <div className="p-3 bg-red-950 border border-red-800 rounded-xl text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Delete confirmation modal */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-sm bg-gray-900 rounded-2xl p-6 space-y-4">
            <h2 className="text-xl font-bold">Profil löschen?</h2>
            <p className="text-gray-400">
              Soll das Profil{" "}
              <span className="text-gray-100 font-semibold">
                &quot;{deleteTarget.name}&quot;
              </span>{" "}
              wirklich gelöscht werden? Diese Aktion kann nicht rückgängig
              gemacht werden.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="flex-1 min-h-[56px] bg-gray-800 text-gray-300 font-semibold rounded-xl active:bg-gray-700"
              >
                Abbrechen
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 min-h-[56px] bg-red-600 text-white font-semibold rounded-xl active:bg-red-700"
              >
                Löschen
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-end justify-center">
          <div className="w-full max-w-lg bg-gray-900 rounded-t-2xl p-6 space-y-4 safe-bottom">
            <h2 className="text-xl font-bold">
              {editing ? "Profil bearbeiten" : "Neues Profil"}
            </h2>

            {error && (
              <div className="p-3 bg-red-950 border border-red-800 rounded-xl text-red-300 text-sm">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <input
                type="text"
                placeholder="Name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full min-h-[48px] px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500"
              />

              <div className="flex gap-3">
                {(["125L", "100L", "50L"] as const).map((mag) => (
                  <button
                    key={mag}
                    onClick={() => setForm({ ...form, magnification: mag })}
                    className={`flex-1 min-h-[48px] rounded-xl font-semibold ${
                      form.magnification === mag
                        ? "bg-blue-600 text-white"
                        : "bg-gray-800 text-gray-400 border border-gray-700"
                    }`}
                  >
                    {mag}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-3 gap-3">
                <input
                  type="number"
                  placeholder="kV"
                  value={form.voltage}
                  onChange={(e) =>
                    setForm({ ...form, voltage: e.target.value })
                  }
                  className="min-h-[48px] px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500"
                />
                <input
                  type="number"
                  placeholder="uA"
                  value={form.ampere}
                  onChange={(e) =>
                    setForm({ ...form, ampere: e.target.value })
                  }
                  className="min-h-[48px] px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500"
                />
                <input
                  type="number"
                  placeholder="Grad"
                  value={form.rotationDegrees}
                  onChange={(e) =>
                    setForm({ ...form, rotationDegrees: e.target.value })
                  }
                  className="min-h-[48px] px-4 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500"
                />
              </div>

              <textarea
                placeholder="Beschreibung (optional)"
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                rows={2}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-gray-100 placeholder-gray-500 resize-none"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowForm(false)}
                className="flex-1 min-h-[56px] bg-gray-800 text-gray-300 font-semibold rounded-xl active:bg-gray-700"
              >
                Abbrechen
              </button>
              <button
                onClick={handleSave}
                disabled={!form.name || saving}
                className={`flex-1 min-h-[56px] font-semibold rounded-xl ${
                  form.name && !saving
                    ? "bg-blue-600 text-white active:bg-blue-700"
                    : "bg-gray-800 text-gray-600 cursor-not-allowed"
                }`}
              >
                {saving ? "Speichern..." : "Speichern"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Profile list */}
      <div className="space-y-3">
        {profiles.length === 0 && (
          <p className="text-center text-gray-500 py-12">
            Noch keine Profile erstellt.
          </p>
        )}
        {profiles.map((profile) => (
          <ProfileCard
            key={profile.id}
            profile={profile}
            isActive={activeProfileId === profile.id}
            onEdit={() => openEdit(profile)}
            onDelete={() => handleDelete(profile)}
            onSelect={() => handleSelectActive(profile)}
          />
        ))}
      </div>
    </div>
  );
}
