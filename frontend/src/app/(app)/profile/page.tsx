"use client";

import { useState, useEffect, useMemo } from "react";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";
import { ArrowLeft, Settings, Linkedin, Twitter } from "lucide-react";
import SessionHistory from "@/components/userprofile/SessionHistory";
import InvoiceHistory from "@/components/userprofile/InvoiceHistory";
import Link from "next/link";

export default function ProfilePage() {
    const { user } = useAuthStore();
    const [activeTab, setActiveTab] = useState<'profile' | 'sessions' | 'invoices'>('profile');

    // Heartbeat to keep session last_seen_at updated (parity with Web-app)
    useEffect(() => {
        let stopped = false;
        let timer: any;
        const beat = async () => {
            try {
                await authService.ping();
            } catch { }
            if (!stopped) timer = setTimeout(beat, 15000); // every 15s
        };
        beat();
        return () => { stopped = true; if (timer) clearTimeout(timer); };
    }, []);

    const getUserInitials = () => {
        if (!user?.first_name && !user?.email) return "U";
        if (user.first_name && user.last_name) {
            return (user.first_name[0] + user.last_name[0]).toUpperCase();
        }
        return user.email[0].toUpperCase();
    };

    const displayName = useMemo(() => {
        if (user?.first_name || user?.last_name) {
            return [user.first_name, user.last_name].filter(Boolean).join(' ');
        }
        return user?.email?.split('@')[0] || 'User';
    }, [user]);

    // Use Web-app styles adapted for marine (standard tailwind)
    const darkMode = false; // TODO: Hook into theme if available
    
    // Fallback/Mock data if not available in AuthUser (marine's AuthUser is slimmer)
    // We would need to fetch full profile from /auth/me if we want all details like phone/company/bio
    // For now we use what's in store + assumption that store might update or we fetch "me"
    
    const [profileData, setProfileData] = useState<any>(user);

    useEffect(() => {
        // Fetch full profile data on mount
        const fetchProfile = async () => {
            try {
                const data = await authService.me();
                setProfileData(data);
            } catch (e) {
                console.error("Failed to fetch profile", e);
            }
        };
        fetchProfile();
    }, []);


    return (
        <div className="min-h-screen bg-slate-50 dark:bg-gray-900 transition-colors duration-200">
            <main className="flex-1 overflow-auto p-4 md:p-6">
                <div className="w-full mx-auto space-y-8 max-w-5xl">
                    {/* Profile Card */}
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border border-slate-200 dark:border-gray-700">
                         {/* Header Section */}
                        <div className="relative">
                             <div className="h-32 bg-gradient-to-r from-slate-200 to-slate-100 dark:from-gray-700 dark:to-gray-800">
                                 <div className="absolute top-4 left-4">
                                     <Link
                                         href="/dashboard" /* Accessing dashboard route */
                                         className="p-2 bg-white/50 hover:bg-white/80 rounded-full text-slate-700 transition-colors backdrop-blur-sm"
                                     >
                                         <ArrowLeft className="h-5 w-5" />
                                     </Link>
                                 </div>
                             </div>

                             {/* Profile Info */}
                            <div className="px-6 pb-8 w-full relative">
                                <div className="-mt-12 mb-4">
                                    <div className="w-24 h-24 rounded-full flex items-center justify-center bg-blue-600 text-white text-3xl font-semibold shadow-md border-4 border-white dark:border-gray-800">
                                        {getUserInitials()}
                                    </div>
                                </div>
                                
                                <div className="mb-6">
                                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{displayName}</h2>
                                    <p className="text-slate-500 dark:text-gray-400">{user?.email}</p>
                                    
                                    <div className="mt-3 flex flex-wrap gap-2">
                                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                                            {profileData?.role || 'User'}
                                        </span>
                                        {profileData?.plan_name && (
                                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300">
                                                Plan: {profileData.plan_name}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Tabs */}
                                <div className="border-b border-slate-200 dark:border-gray-700 mb-6">
                                    <nav className="-mb-px flex space-x-8">
                                        <button
                                            onClick={() => setActiveTab('profile')}
                                            className={`${activeTab === 'profile'
                                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:text-gray-400 dark:hover:text-gray-300'
                                                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                                        >
                                            Profile
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('sessions')}
                                            className={`${activeTab === 'sessions'
                                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:text-gray-400 dark:hover:text-gray-300'
                                                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                                        >
                                            Sessions
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('invoices')}
                                            className={`${activeTab === 'invoices'
                                                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300 dark:text-gray-400 dark:hover:text-gray-300'
                                                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                                        >
                                            Invoices
                                        </button>
                                    </nav>
                                </div>

                                {/* Tab Content */}
                                <div>
                                    {activeTab === 'profile' && (
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            <div className="space-y-4">
                                                <div>
                                                    <h4 className="text-sm font-medium text-slate-500 dark:text-gray-400 uppercase tracking-wider">Contact Information</h4>
                                                    <div className="mt-3 space-y-3">
                                                        <div>
                                                            <div className="text-xs text-slate-400 dark:text-gray-500">Email</div>
                                                            <div className="text-sm font-medium text-slate-900 dark:text-gray-200 break-all">{profileData?.email}</div>
                                                        </div>
                                                        <div>
                                                            <div className="text-xs text-slate-400 dark:text-gray-500">Phone</div>
                                                            <div className="text-sm font-medium text-slate-900 dark:text-gray-200">{profileData?.phone || '—'}</div>
                                                        </div>
                                                        <div>
                                                            <div className="text-xs text-slate-400 dark:text-gray-500">Website</div>
                                                            <div className="text-sm font-medium text-slate-900 dark:text-gray-200">{profileData?.website || '—'}</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="space-y-4">
                                                <div>
                                                     <h4 className="text-sm font-medium text-slate-500 dark:text-gray-400 uppercase tracking-wider">Company Information</h4>
                                                     <div className="mt-3 space-y-3">
                                                         <div>
                                                             <div className="text-xs text-slate-400 dark:text-gray-500">Company Name</div>
                                                             <div className="text-sm font-medium text-slate-900 dark:text-gray-200">{profileData?.company || '—'}</div>
                                                         </div>
                                                     </div>
                                                </div>
                                                
                                                {profileData?.bio && (
                                                    <div>
                                                        <h4 className="text-sm font-medium text-slate-500 dark:text-gray-400 uppercase tracking-wider">Bio</h4>
                                                        <p className="mt-2 text-sm text-slate-700 dark:text-gray-300">{profileData.bio}</p>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === 'sessions' && (
                                        <SessionHistory />
                                    )}

                                    {activeTab === 'invoices' && (
                                        <InvoiceHistory />
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
