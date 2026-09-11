import React, { useState, useEffect } from 'react';
import { useAuth } from './hooks/useAuth';
import { usePlatformRouter } from './hooks/usePlatformRouter';
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
  const { user, activePortal, setActivePortal } = useAuth();
  const { route, navigate, navigateToCatalog } = usePlatformRouter();

  const isCatalog = route.portal === 'catalog';

  // Sync route portal with auth active portal when navigating directly via URL
  useEffect(() => {
    if (['patient', 'doctor', 'hospital', 'admin'].includes(route.portal)) {
      if (route.portal !== activePortal) {
        setActivePortal(route.portal);
      }
    }
  }, [route.portal, activePortal, setActivePortal]);

  if (!user) {
    return <AuthScreen />;
  }

  const context = {
    hospital_id: user.hospital_id || undefined,
    doctor_id: user.role === 'DOCTOR' ? user.identifier : undefined,
    patient_id: user.role === 'PATIENT' ? user.identifier : undefined,
  };

  const handlePortalSwitch = (portal: string) => {
    setActivePortal(portal);
    navigate(`/${portal}`);
  };

  const handleToggleCatalog = () => {
    if (isCatalog) {
      navigate(`/${activePortal}`);
    } else {
      navigateToCatalog(
        user.role === 'PLATFORM_ADMIN'
          ? 'admin'
          : user.role === 'HOSPITAL_ADMIN'
          ? 'hospital'
          : user.role === 'DOCTOR'
          ? 'doctor'
          : 'patient',
        'overview'
      );
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Navbar
        isCatalogOpen={isCatalog}
        onToggleCatalog={handleToggleCatalog}
        activePortal={activePortal}
        onSelectPortal={handlePortalSwitch}
      />

      {isCatalog ? (
        <div className="flex-1 flex overflow-hidden">
          {/* 49-Page Catalog Navigation Sidebar */}
          <CatalogSidebar
            currentRole={route.catalogRole || user.role}
            selectedPage={
              route.catalogRole && route.catalogPageId
                ? { role: route.catalogRole, page_id: route.catalogPageId }
                : null
            }
            onSelectPage={(role, page) => navigateToCatalog(role, page.page_id)}
            onBackToDashboard={() => navigate(`/${activePortal}`)}
          />

          {/* Dynamic 49-Page Viewer Content */}
          <main className="flex-1 overflow-y-auto">
            {route.catalogRole && route.catalogPageId ? (
              <DynamicPageViewer
                role={route.catalogRole}
                page={{
                  page_id: route.catalogPageId,
                  page_number: 1,
                  title: route.catalogPageId.replace('_', ' ').toUpperCase(),
                  description: 'Dynamic enterprise page synchronized via deep URL hash.',
                  category: 'Enterprise',
                  icon: 'layers',
                  default_actions: ['inspect', 'export_telemetry'],
                }}
                context={context}
                onBackToWorkspace={() => navigate(`/${activePortal}`)}
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
          {(route.portal === 'patient' || activePortal === 'patient') && <PatientPortal />}
          {(route.portal === 'doctor' || activePortal === 'doctor') && <DoctorPortal />}
          {(route.portal === 'hospital' || activePortal === 'hospital') && <HospitalPortal />}
          {(route.portal === 'admin' || activePortal === 'admin') && <PlatformAdminPortal />}
        </main>
      )}
    </div>
  );
};
