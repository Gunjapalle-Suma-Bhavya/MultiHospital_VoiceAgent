import React, { useState, useEffect, Suspense, lazy } from 'react';
import { useAuth } from './hooks/useAuth';
import { usePlatformRouter } from './hooks/usePlatformRouter';
import { Navbar } from './components/Navbar';
import { CatalogSidebar } from './components/CatalogSidebar';
import { LandingPage } from './modules/landing/LandingPage';
import { PatientPortal } from './modules/patient';
import { CatalogPage } from './api/client';

// Lazy-loaded portals & heavy catalog views for route-level code splitting
const DoctorPortal = lazy(() => import('./modules/doctor').then((m) => ({ default: m.DoctorPortal })));
const HospitalPortal = lazy(() => import('./modules/hospital').then((m) => ({ default: m.HospitalPortal })));
const PlatformAdminPortal = lazy(() => import('./modules/admin').then((m) => ({ default: m.PlatformAdminPortal })));
const DynamicPageViewer = lazy(() => import('./components/DynamicPageViewer').then((m) => ({ default: m.DynamicPageViewer })));

const WorkspaceLoader: React.FC = () => (
  <div className="flex-1 flex flex-col items-center justify-center p-16 space-y-3">
    <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
      Loading Clinical Workspace...
    </span>
  </div>
);

export const App: React.FC = () => {
  const { user, activePortal, setActivePortal } = useAuth();
  const { route, navigate, navigateToCatalog } = usePlatformRouter();

  const isCatalog = route.portal === 'catalog';

  // Strict Role-Authorized Workspace Isolation
  const roleAuthorizedPortal =
    user?.role === 'PATIENT'
      ? 'patient'
      : user?.role === 'DOCTOR'
      ? 'doctor'
      : user?.role === 'PLATFORM_ADMIN'
      ? 'admin'
      : 'hospital';

  // Force active portal to the user's role-authorized workspace
  useEffect(() => {
    if (user && activePortal !== roleAuthorizedPortal) {
      setActivePortal(roleAuthorizedPortal);
    }
  }, [user, activePortal, roleAuthorizedPortal, setActivePortal]);

  if (!user) {
    return <LandingPage />;
  }

  const context = {
    hospital_id: user.hospital_id || undefined,
    doctor_id: user.role === 'DOCTOR' ? user.identifier : undefined,
    patient_id: user.role === 'PATIENT' ? user.identifier : undefined,
  };

  const handlePortalSwitch = (portal: string) => {
    // Only allow switching if user's role permits it
    if (user.role === 'PLATFORM_ADMIN' || portal === roleAuthorizedPortal) {
      setActivePortal(portal);
      navigate(`/${portal}`);
    }
  };

  const handleToggleCatalog = () => {
    if (user.role !== 'PLATFORM_ADMIN') return;
    if (isCatalog) {
      navigate(`/${activePortal}`);
    } else {
      navigateToCatalog('admin', 'overview');
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 transition-colors duration-200">
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
              <Suspense fallback={<WorkspaceLoader />}>
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
              </Suspense>
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
          {roleAuthorizedPortal === 'patient' && (
            <PatientPortal initialTab={route.view} />
          )}
          <Suspense fallback={<WorkspaceLoader />}>
            {roleAuthorizedPortal === 'doctor' && (
              <DoctorPortal initialTab={route.view} />
            )}
            {roleAuthorizedPortal === 'hospital' && (
              <HospitalPortal initialTab={route.view} />
            )}
            {roleAuthorizedPortal === 'admin' && (
              <PlatformAdminPortal initialTab={route.view} />
            )}
          </Suspense>
        </main>
      )}
    </div>
  );
};
