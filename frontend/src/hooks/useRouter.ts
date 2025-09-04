
import { useState, useEffect } from 'react';

const useRouter = () => {
  const [path, setPath] = useState(window.location.pathname);

  const handleLocationChange = () => {
    setPath(window.location.pathname);
  };

  const push = (newPath: string) => {
    window.history.pushState({}, '', newPath);
    handleLocationChange();
  };

  useEffect(() => {
    window.addEventListener('popstate', handleLocationChange);
    return () => {
      window.removeEventListener('popstate', handleLocationChange);
    };
  }, []);

  return { path, push };
};

export default useRouter;
