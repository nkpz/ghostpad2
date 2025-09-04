import { ReactNode } from "react";

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: Readonly<MainLayoutProps>) {
  return (
    <div className="flex-1 flex gap-4 px-6 pb-6 min-h-0 relative">
      {children}
    </div>
  );
}