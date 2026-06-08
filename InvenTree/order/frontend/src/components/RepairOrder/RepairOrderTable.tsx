import React, { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TableSortLabel,
  Paper,
  IconButton,
  Tooltip,
  Chip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Checkbox,
  FormControlLabel,
  Grid,
  InputAdornment,
  CircularProgress,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format } from 'date-fns';

// ---------------------------------------------------------------------------
// Types & Interfaces
// ---------------------------------------------------------------------------

interface RepairOrder {
  id: number;
  order_id: string;
  description: string;
  customer_unit: {
    id: number;
    serial: string;
    part_detail: {
      id: number;
      name: string;
      IPN: string;
    };
  } | null;
  status: RepairOrderStatus;
  creation_date: string;
  target_date: string | null;
  completed_date: string | null;
  created_by: {
    id: number;
    username: string;
  } | null;
  responsible: {
    id: number;
    username: string;
  } | null;
  parts_used_count: number;
  labor_hours: number;
  total_cost: number;
  notes: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

type RepairOrderStatus =
  | 'pending'
  | 'in_progress'
  | 'awaiting_parts'
  | 'completed'
  | 'cancelled'
  | 'on_hold';

type SortField = keyof RepairOrder | 'customer_unit__serial' | 'customer_unit__part_detail__name';

interface SortConfig {
  field: SortField;
  direction: 'asc' | 'desc';
}

interface FilterState {
  search: string;
  status: RepairOrderStatus | '';
  priority: string;
  dateFrom: Date | null;
  dateTo: Date | null;
  createdBy: string;
  responsible: string;
  showArchived: boolean;
}

interface RepairOrderTableProps {
  /** Initial data to display (can be empty for server-side loading) */
  initialOrders?: RepairOrder[];
  /** Enable server-side pagination/sorting/filtering */
  serverSide?: boolean;
  /** Base URL for API calls (used when serverSide is true) */
  apiBaseUrl?: string;
  /** Callback when an order is selected */
  onOrderSelect?: (order: RepairOrder) => void;
  /** Callback when the new order button is clicked */
  onCreateOrder?: () => void;
  /** Callback when edit action is triggered */
  onEditOrder?: (order: RepairOrder) => void;
  /** Callback when delete action is triggered */
  onDeleteOrder?: (order: RepairOrder) => void;
  /** Callback when view action is triggered */
  onViewOrder?: (order: RepairOrder) => void;
  /** Custom action buttons to render per row */
  renderActions?: (order: RepairOrder) => React.ReactNode;
  /** Custom filter components to render above the table */
  renderCustomFilters?: React.ReactNode;
  /** Loading state override */
  loading?: boolean;
  /** Error state */
  error?: string | null;
  /** Empty state message */
  emptyMessage?: string;
  /** Title for the table */
  title?: string;
  /** Enable row selection */
  selectable?: boolean;
  /** Callback when selected rows change */
  onSelectionChange?: (selectedIds: number[]) => void;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<RepairOrderStatus, { label: string; color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' }> = {
  pending: { label: 'Pending', color: 'default' },
  in_progress: { label: 'In Progress', color: 'primary' },
  awaiting_parts: { label: 'Awaiting Parts', color: 'warning' },
  completed: { label: 'Completed', color: 'success' },
  cancelled: { label: 'Cancelled', color: 'error' },
  on_hold: { label: 'On Hold', color: 'secondary' },
};

const PRIORITY_CONFIG: Record<string, { label: string; color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' }> = {
  low: { label: 'Low', color: 'default' },
  medium: { label: 'Medium', color: 'info' },
  high: { label: 'High', color: 'warning' },
  critical: { label: 'Critical', color: 'error' },
};

const DEFAULT_PAGE_SIZE = 25;
const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// ---------------------------------------------------------------------------
// Helper Functions
// ---------------------------------------------------------------------------

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return '-';
  try {
    return format(new Date(dateStr), 'yyyy-MM-dd HH:mm');
  } catch {
    return dateStr;
  }
};

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount);
};

// ---------------------------------------------------------------------------
// Sub-Components
// ---------------------------------------------------------------------------

interface StatusChipProps {
  status: RepairOrderStatus;
}

const StatusChip: React.FC<StatusChipProps> = React.memo(({ status }) => {
  const config = STATUS_CONFIG[status] || { label: status, color: 'default' as const };
  return <Chip label={config.label} color={config.color} size="small" variant="outlined" />;
});

StatusChip.displayName = 'StatusChip';

interface PriorityChipProps {
  priority: string;
}

const PriorityChip: React.FC<PriorityChipProps> = React.memo(({ priority }) => {
  const config = PRIORITY_CONFIG[priority] || { label: priority, color: 'default' as const };
  return <Chip label={config.label} color={config.color} size="small" />;
});

PriorityChip.displayName = 'PriorityChip';

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

const RepairOrderTable: React.FC<RepairOrderTableProps> = ({
  initialOrders = [],
  serverSide = false,
  apiBaseUrl = '/api/repair-order/',
  onOrderSelect,
  onCreateOrder,
  onEditOrder,
  onDeleteOrder,
  onViewOrder,
  renderActions,
  renderCustomFilters,
  loading: externalLoading,
  error: externalError,
  emptyMessage = 'No repair orders found.',
  title = 'Repair Orders',
  selectable = false,
  onSelectionChange,
}) => {
  const navigate = useNavigate();

  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------

  const [orders, setOrders] = useState<RepairOrder[]>(initialOrders);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(DEFAULT_PAGE_SIZE);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'creation_date', direction: 'desc' });
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    status: '',
    priority: '',
    dateFrom: null,
    dateTo: null,
    createdBy: '',
    responsible: '',
    showArchived: false,
  });
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [totalCount, setTotalCount] = useState<number>(initialOrders.length);

  // -----------------------------------------------------------------------
  // Computed Values
  // -----------------------------------------------------------------------

  const isLoading = externalLoading !== undefined ? externalLoading : loading;
  const displayError = externalError !== undefined ? externalError : error;

  // -----------------------------------------------------------------------
  // API Calls (Server-Side Mode)
  // -----------------------------------------------------------------------

  const fetchOrders = useCallback(async () => {
    if (!serverSide) return;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('page', String(page + 1));
      params.append('page_size', String(rowsPerPage));
      params.append('ordering', `${sortConfig.direction === 'desc' ? '-' : ''}${sortConfig.field}`);

      if (filters.search) params.append('search', filters.search);
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.createdBy) params.append('created_by', filters.createdBy);
      if (filters.responsible) params.append('responsible', filters.responsible);
      if (filters.dateFrom) params.append('created_after', filters.dateFrom.toISOString());
      if (filters.dateTo) params.append('created_before', filters.dateTo.toISOString());
      if (filters.showArchived) params.append('archived', 'true');

      const response = await fetch(`${apiBaseUrl}?${params.toString()}`, {
        headers: {
          'Content-Type': 'application/json',
          // Include auth headers as needed by InvenTree
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();
      setOrders(data.results || data);
      setTotalCount(data.count || data.length || 0);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch repair orders';
      setError(message);
      setOrders([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [serverSide, page, rowsPerPage, sortConfig, filters, apiBaseUrl]);

  // Fetch on mount and when dependencies change (server-side only)
  React.useEffect(() => {
    if (serverSide) {
      fetchOrders();
    }
  }, [fetchOrders, serverSide]);

  // Update local orders when initialOrders prop changes (client-side mode)
  React.useEffect(() => {
    if (!serverSide) {
      setOrders(initialOrders);
      setTotalCount(initialOrders.length);
    }
  }, [initialOrders, serverSide]);

  // -----------------------------------------------------------------------
  // Client-Side Sorting & Filtering
  // -----------------------------------------------------------------------

  const filteredOrders = useMemo(() => {
    if (serverSide) return orders;

    let result = [...orders];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (order) =>
          order.order_id.toLowerCase().includes(searchLower) ||
          order.description?.toLowerCase().includes(searchLower) ||
          order.customer_unit?.serial?.toLowerCase().includes(searchLower) ||
          order.customer_unit?.part_detail?.name?.toLowerCase().includes(searchLower) ||
          order.customer_unit?.part_detail?.IPN?.toLowerCase().includes(searchLower)
      );
    }

    // Status filter
    if (filters.status) {
      result = result.filter((order) => order.status === filters.status);
    }

    // Priority filter
    if (filters.priority) {
      result = result.filter((order) => order.priority === filters.priority);
    }

    // Date range filter
    if (filters.dateFrom) {
      const from = filters.dateFrom.getTime();
      result = result.filter((order) => new Date(order.creation_date).getTime() >= from);
    }
    if (filters.dateTo) {
      const to = filters.dateTo.getTime();
      result = result.filter((order) => new Date(order.creation_date).getTime() <= to);
    }

    // Created by filter
    if (filters.createdBy) {
      const createdByLower = filters.createdBy.toLowerCase();
      result = result.filter(
        (order) => order.created_by?.username?.toLowerCase().includes(createdByLower)
      );
    }

    // Responsible filter
    if (filters.responsible) {
      const responsibleLower = filters.responsible.toLowerCase();
      result = result.filter(
        (order) => order.responsible?.username?.toLowerCase().includes(responsibleLower)
      );
    }

    // Sorting
    result.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortConfig.field) {
        case 'customer_unit__serial':
          aValue = a.customer_unit?.serial || '';
          bValue = b.customer_unit?.serial || '';
          break;
        case 'customer_unit__part_detail__name':
          aValue = a.customer_unit?.part_detail?.name || '';
          bValue = b.customer_unit?.part_detail?.name || '';
          break;
        default:
          aValue = a[sortConfig.field as keyof RepairOrder];
          bValue = b[sortConfig.field as keyof RepairOrder];
      }

      if (aValue == null) return 1;
      if (bValue == null) return -1;

      if (typeof aValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return sortConfig.direction === 'asc' ? comparison : -comparison;
      }

      return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
    });

    return result;
  }, [orders, filters, sortConfig, serverSide]);

  // Client-side pagination
  const paginatedOrders = useMemo(() => {
    if (serverSide) return orders;
    const start = page * rowsPerPage;
    return filteredOrders.slice(start, start + rowsPerPage);
  }, [filteredOrders, page, rowsPerPage, serverSide, orders]);

  // -----------------------------------------------------------------------
  // Event Handlers
  // -----------------------------------------------------------------------

  const handleSort = useCallback((field: SortField) => {
    setSortConfig((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
    setPage(0);
  }, []);

  const handleChangePage = useCallback((_event: unknown, newPage: number) => {
    setPage(newPage);
  }, []);

  const handleChangeRowsPerPage = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  }, []);

  const handleFilterChange = useCallback((key: keyof FilterState, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
  }, []);

  const handleResetFilters = useCallback(() => {
    setFilters({
      search: '',
      status: '',
      priority: '',
      dateFrom: null,
      dateTo: null,
      createdBy: '',
      responsible: '',
      showArchived: false,
    });
    setPage(0);
  }, []);

  const handleRefresh = useCallback(() => {
    if (serverSide) {
      fetchOrders();
    }
  }, [fetchOrders, serverSide]);

  const handleSelectAll = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newSelected = event.target.checked
        ? paginatedOrders.map((order) => order.id)
        : [];
      setSelectedIds(newSelected);
      onSelectionChange?.(newSelected);
    },
    [paginatedOrders, onSelectionChange]
  );

  const handleSelectOne = useCallback(
    (id: number) => {
      const currentIndex = selectedIds.indexOf(id);
      const newSelected = [...selectedIds];

      if (currentIndex === -1) {
        newSelected.push(id);
      } else {
        newSelected.splice(currentIndex, 1);
      }

      setSelectedIds(newSelected);
      onSelectionChange?.(newSelected);
    },
    [selectedIds, onSelectionChange]
  );

  const handleRowClick = useCallback(
    (order: RepairOrder) => {
      if (onOrderSelect) {
        onOrderSelect(order);
      }
    },
    [onOrderSelect]
  );

  // -----------------------------------------------------------------------
  // Render Helpers
  // -----------------------------------------------------------------------

  const renderSortableHeader = (label: string, field: SortField) => (
    <TableSortLabel
      active={sortConfig.field === field}
      direction={sortConfig.field === field ? sortConfig.direction : 'asc'}
      onClick={() => handleSort(field)}
    >
      {label}
    </TableSortLabel>
  );

  const renderFilterSection = () => (
    <Box sx={{ mb: 2 }}>
      <Grid container spacing={2} alignItems="center">
        {/* Search */}
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            fullWidth
            size="small"
            placeholder="Search orders..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
        </Grid>

        {/* Status Filter */}
        <Grid item xs={6} sm={3} md={2}>
          <FormControl fullWidth size="small">
            <InputLabel>Status</InputLabel>
            <Select
              value={filters.status}
              label="Status"
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {Object.entries(STATUS_CONFIG).map(([value, config]) => (
                <MenuItem key