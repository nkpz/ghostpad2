import {
  useState,
  useEffect,
  useImperativeHandle,
  forwardRef,
  useRef,
} from "react";

interface TableDisplayProps {
  loadData?: () => Promise<Record<string, any>>;
  props?: {
    height?: string;
    show_refresh?: boolean;
    placeholder?: string;
    columns?: Array<{
      key: string;
      label: string;
      format?: "text" | "number";
    }>;
  };
  value?: Record<string, any>;
  onChange?: (value: Record<string, any>) => void;
}

export interface TableDisplayRef {
  refresh: () => void;
}

function renderTableContent(
  loading: boolean,
  hasData: boolean,
  data: Record<string, any>,
  columns: Array<{
    key: string;
    label: string;
    format?: "text" | "number";
  }>,
  placeholder?: string
) {
  if (loading) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        Loading...
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        {placeholder || "No data available."}
      </div>
    );
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b bg-muted/50">
          {columns.map((column) => (
            <th key={column.key} className="text-left p-2 font-medium">
              {column.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Object.entries(data).map(([key, value]) => (
          <tr key={key} className="border-b last:border-b-0">
            <td className="p-2 truncate">{key}</td>
            <td className="p-2 font-mono">
              {columns[1]?.format === "number"
                ? Number(value)
                : String(value)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export const TableDisplay = forwardRef<TableDisplayRef, TableDisplayProps>(
  ({ loadData, props, value, onChange }, ref) => {
    const [data, setData] = useState<Record<string, any>>(value || {});
    const [loading, setLoading] = useState(false);
    const hasRun = useRef(false);

    const fetchData = async () => {
      if (!loadData) return;

      setLoading(true);
      try {
        const tableData = await loadData();
        setData(tableData);
        onChange?.(tableData);
      } catch (error) {
        console.error("Failed to load table data:", error);
      } finally {
        setLoading(false);
      }
    };

    useEffect(() => {
      if (hasRun.current) return;
      hasRun.current = true;

      if (loadData) {
        fetchData();
      }
    }, []); // Only run once on mount

    const handleRefresh = () => {
      fetchData();
    };

    useImperativeHandle(ref, () => ({
      refresh: fetchData,
    }));

    const hasData = Object.keys(data).length > 0;
    const columns = props?.columns || [
      { key: "key", label: "Name", format: "text" as const },
      { key: "value", label: "Value", format: "text" as const },
    ];

    return (
      <div className="space-y-2">
        {props?.show_refresh && (
          <div className="flex justify-end">
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="text-xs px-2 py-1 bg-muted hover:bg-muted/80 rounded"
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>
        )}

        <div
          className="rounded border bg-muted/30 overflow-auto"
          style={{ height: props?.height }}
        >
          {renderTableContent(loading, hasData, data, columns, props?.placeholder)}
        </div>
      </div>
    );
  }
);
