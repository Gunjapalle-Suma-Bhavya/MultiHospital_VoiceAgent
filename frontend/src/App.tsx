import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';
import { Navbar } from './components/Navbar';
import { CatalogSidebar } from './components/CatalogSidebar';
import { DynamicPageViewer } from './components/DynamicPageViewer';
import { AuthScreen } from './modules/auth/AuthScreen';
import { PatientPortal } from './modules/patient';
import { DoctorPortal } from './modules/doctor';
import { HospitalPortal } from './modules/hospital';
import { PlatformAdminPortal } from './modules/admin';
import { CatalogPage } from './api/client';

export const App: React.FC = () => {
  const { user, activePortal } = useAuth();
  const [isCatalogOpen, setIsCatalogOpen] = useState(false);
  const [selectedCatalogPage, setSelectedCatalogPage] = useState<{
    role: string;
    page: CatalogPage;
  } | null>(null);

  if (!user) {
    return <AuthScreen />;
  }

  const context = {
    hospital_id: user.hospital_id || undefined,
    doctor_id: user.role === 'DOCTOR' ? user.identifier : undefined,
    patient_id: user.role === 'PATIENT' ? user.identifier : undefined,
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navbar
        isCatalogOpen={isCatalogOpen}
        onToggleCatalog={() => setIsCatalogOpen((prev) => !prev)}
      />

      {isCatalogOpen ? (
        <div className="flex-1 flex overflow-hidden">
          {/* 49-Page Catalog Navigation Sidebar */}
          <CatalogSidebar
            currentRole={user.role}
            selectedPage={
              selectedCatalogPage
                ? { role: selectedCatalogPage.role, page_id: selectedCatalogPage.page.page_id }
                : null
            }
            onSelectPage={(role, page) => setSelectedCatalogPage({ role, page })}
            onBackToDashboard={() => setIsCatalogOpen(false)}
          />

          {/* Dynamic 49-Page Viewer Content */}
          <main className="flex-1 overflow-y-auto">
            {selectedCatalogPage ? (
              <DynamicPageViewer
                role={selectedCatalogPage.role}
                page={selectedCatalogPage.page}
                context={context}
                onBackToWorkspace={() => setIsCatalogOpen(false)}
              />
            ) : (
              <div className="p-12 text-center text-slate-400 space-y-3">
                <div className="text-xl font-bold text-white">49-Page Platform Catalog Explorer</div>
                <p className="text-xs max-w-md mx-auto text-slate-400">
                  Select any of the 49 canonical pages from the sidebar on the left to inspect its live
                  telemetry, KPIs, records, and executable actions.
                </p>
              </div>
            )}
          </main>
        </div>
      ) : (
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
          {activePortal === 'patient' && <PatientPortal />}
          {activePortal === 'doctor' && <DoctorPortal />}
          {activePortal === 'hospital' && <HospitalPortal />}
          {activePortal === 'admin' && <PlatformAdminPortal />}
        </main>
      )}
    </div>
  );
};

