
import React, { createContext, useContext, useMemo } from 'react';
import useRouter from '../../hooks/useRouter';

const RouterContext = createContext<{ path: string; push: (newPath: string) => void; }>({ path: '/', push: () => {} });

export const useRouterContext = () => useContext(RouterContext);

const Router = ({ children }: { children: React.ReactNode }) => {
  const { path, push } = useRouter();

  const value = useMemo(() => ({ path, push }), [path, push]);

  return (
    <RouterContext.Provider value={value}>
      {children}
    </RouterContext.Provider>
  );
};

export default Router;
