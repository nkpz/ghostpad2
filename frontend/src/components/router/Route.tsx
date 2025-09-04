
import React from 'react';
import { useRouterContext } from './Router';

const Route = ({ path, children }: { path: string; children: React.ReactNode }) => {
  const { path: currentPath } = useRouterContext();

  // Handle dynamic routes with parameters
  const match = (routePath: string, currentPath: string) => {
    const routeParts = routePath.split('/').filter(p => p);
    const currentParts = currentPath.split('/').filter(p => p);

    if (routeParts.length !== currentParts.length) {
      return null;
    }

    const params: { [key: string]: string } = {};
    for (let i = 0; i < routeParts.length; i++) {
      if (routeParts[i].startsWith(':')) {
        const paramName = routeParts[i].substring(1);
        params[paramName] = currentParts[i];
      } else if (routeParts[i] !== currentParts[i]) {
        return null;
      }
    }

    return params;
  };

  const params = match(path, currentPath);

  if (params) {
    // Inject params into children
    return <>{React.Children.map(children, child => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child, { params } as any);
      }
      return child;
    })}</>
  }

  return null;
};

export default Route;
