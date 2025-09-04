interface MobileOverlayProps {
  isSettingsSidebarOpen: boolean;
  isConversationsSidebarOpen: boolean;
  toggleSettingsSidebar: () => void;
  toggleConversationsSidebar: () => void;
}

export function MobileOverlay({
  isSettingsSidebarOpen,
  isConversationsSidebarOpen,
  toggleSettingsSidebar,
  toggleConversationsSidebar,
}: Readonly<MobileOverlayProps>) {
  return (
    <>
      {/* Mobile overlay backdrops */}
      {isSettingsSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-[5] xl:hidden"
          onClick={toggleSettingsSidebar}
        />
      )}
      {isConversationsSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-[5] xl:hidden"
          onClick={toggleConversationsSidebar}
        />
      )}
    </>
  );
}