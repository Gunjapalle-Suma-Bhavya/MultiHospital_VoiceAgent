import { useState, useEffect, useCallback } from 'react';

export interface PlatformRoute {
  portal: 'patient' | 'doctor' | 'hospital' | 'admin' | 'catalog';
  view?: string;
  catalogRole?: string;
  catalogPageId?: string;
}

export function parseHash(hash: string): PlatformRoute {
  const clean = hash.replace(/^#\/?/, '').trim();
  if (!clean) {
    return { portal: 'patient', view: 'voice' };
  }

  const parts = clean.split('/');

  if (parts[0] === 'catalog') {
    return {
      portal: 'catalog',
      catalogRole: parts[1] || 'admin',
      catalogPageId: parts[2] || 'overview',
    };
  }

  if (['patient', 'doctor', 'hospital', 'admin'].includes(parts[0])) {
    return {
      portal: parts[0] as PlatformRoute['portal'],
      view: parts[1] || undefined,
    };
  }

  return { portal: 'patient', view: 'voice' };
}

export function usePlatformRouter() {
  const [route, setRoute] = useState<PlatformRoute>(() => parseHash(window.location.hash));

  useEffect(() => {
    const onHashChange = () => {
      setRoute(parseHash(window.location.hash));
    };

    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const navigate = useCallback((path: string) => {
    const formatted = path.startsWith('/') ? path : `/${path}`;
    window.location.hash = formatted;
  }, []);

  const navigateToCatalog = useCallback((role: string, pageId: string) => {
    window.location.hash = `/catalog/${role}/${pageId}`;
  }, []);

  return {
    route,
    navigate,
    navigateToCatalog,
  };
}
