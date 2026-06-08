import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  TextField,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Autocomplete,
  Snackbar,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  History as HistoryIcon,
  Print as PrintIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { api } from '../../utils/api';
import { useUserState } from '../../states/UserState';
import { useNotificationState } from '../../states/NotificationState';
import { formatDate } from '../../utils/formatters';
import { StatusRenderer } from '../../components/StatusRenderer';
import { AttachmentPanel } from '../../components/AttachmentPanel';
import { NotesPanel } from '../../components/NotesPanel';
import { StockItemSelect } from '../../components/StockItemSelect';
import { UserSelect } from '../../components/UserSelect';

// Types
interface RepairOrder {
  pk: number;
  order_id: string;
  reference: string;
  description: string;
  customer_unit: number | null;
  customer_unit_detail?: {
    pk: number;
    serial: string;
    part_detail: { pk: number; name: string; IPN: string };
  } | null;
  customer: number | null;
  customer_detail?: {
    pk: number;
    name: string;
    email: string;
  } | null;
  status: number;
  status_text: string;
  creation_date: string;
  target_date: string | null;
  completion_date: string | null;
  responsible: number | null;
  responsible_detail?: {
    pk: number;
    username: string;
    full_name: string;
  } | null;
  parts_used: RepairOrderPart[];
  labor_entries: RepairOrderLabor[];
  notes: string;
  total_cost: number;
  currency: string;
  link: string;
  project: string;
  priority: number;
}

interface RepairOrderPart {
  pk: number;
  part: number;
  part_detail?: {
    pk: number;
    name: string;
    IPN: string;
    description: string;
  };
  stock_item: number | null;
  stock_item_detail?: {
    pk: number;
    serial: string;
    location_detail?: { pk: number; name: string };
  } | null;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  notes: string;
}

interface RepairOrderLabor {
  pk: number;
  description: string;
  hours: number;
  rate: number;
  total_cost: number;
  user: number | null;
  user_detail?: {
    pk: number;
    username: string;
    full_name: string;
  } | null;
  date: string;
}

interface StockItem {
  pk: number;
  serial: string;
  part: number;
  part_detail: {
    pk: number;
    name: string;
    IPN: string;
    description: string;
  };
  quantity: number;
  location: number | null;
  location_detail?: {
    pk: number;
    name: string;
  } | null;
}

interface User {
  pk: number;
  username: string;
  full_name: string;
  email: string;
}

// Constants
const REPAIR_ORDER_STATUSES = [
  { value: 10, label: 'Pending' },
  { value: 20, label: 'In Progress' },
  { value: 30, label: 'On Hold' },
  { value: 40, label: 'Completed' },
  { value: 50, label: 'Cancelled' },
  { value: 60, label: 'Returned' },
];

const PRIORITY_OPTIONS = [
  { value: 0, label: 'Low' },
  { value: 1, label: 'Normal' },
  { value: 2, label: 'High' },
  { value: 3, label: 'Urgent' },
];

// Main Component
const RepairOrderDetail: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const { user } = useUserState();
  const { addNotification } = useNotificationState();

  // State
  const [order, setOrder] = useState<RepairOrder | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [editForm, setEditForm] = useState<Partial<RepairOrder>>({});
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({ open: false, message: '', severity: 'info' });

  // Part dialog state
  const [partDialogOpen, setPartDialogOpen] = useState<boolean>(false);
  const [editingPart, setEditingPart] = useState<RepairOrderPart | null>(null);
  const [partForm, setPartForm] = useState<{
    part: number | null;
    stock_item: number | null;
    quantity: number;
    unit_cost: number;
    notes: string;
  }>({
    part: null,
    stock_item: null,
    quantity: 1,
    unit_cost: 0,
    notes: '',
  });

  // Labor dialog state
  const [laborDialogOpen, setLaborDialogOpen] = useState<boolean>(false);
  const [editingLabor, setEditingLabor] = useState<RepairOrderLabor | null>(null);
  const [laborForm, setLaborForm] = useState<{
    description: string;
    hours: number;
    rate: number;
    user: number | null;
    date: string;
  }>({
    description: '',
    hours: 1,
    rate: 0,
    user: null,
    date: new Date().toISOString().split('T')[0],
  });

  // Fetch order data
  const fetchOrder = useCallback(async () => {
    if (!orderId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/api/order/repair-order/${orderId}/`);
      setOrder(response.data);
      setEditForm({
        description: response.data.description,
        status: response.data.status,
        priority: response.data.priority,
        target_date: response.data.target_date,
        responsible: response.data.responsible,
        customer: response.data.customer,
        customer_unit: response.data.customer_unit,
        project: response.data.project,
        link: response.data.link,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load repair order');
      addNotification({
        type: 'error',
        message: 'Failed to load repair order details',
      });
    } finally {
      setLoading(false);
    }
  }, [orderId, addNotification]);

  useEffect(() => {
    fetchOrder();
  }, [fetchOrder]);

  // Save order details
  const handleSaveOrder = async () => {
    if (!order) return;
    setSaving(true);
    try {
      const response = await api.patch(
        `/api/order/repair-order/${order.pk}/`,
        editForm
      );
      setOrder(response.data);
      setEditing(false);
      setSnackbar({
        open: true,
        message: 'Repair order updated successfully',
        severity: 'success',
      });
      addNotification({
        type: 'success',
        message: 'Repair order updated',
      });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update repair order';
      setSnackbar({
        open: true,
        message: errorMsg,
        severity: 'error',
      });
      addNotification({
        type: 'error',
        message: errorMsg,
      });
    } finally {
      setSaving(false);
    }
  };

  // Cancel editing
  const handleCancelEdit = () => {
    if (order) {
      setEditForm({
        description: order.description,
        status: order.status,
        priority: order.priority,
        target_date: order.target_date,
        responsible: order.responsible,
        customer: order.customer,
        customer_unit: order.customer_unit,
        project: order.project,
        link: order.link,
      });
    }
    setEditing(false);
  };

  // Add/Edit part
  const handleOpenPartDialog = (part?: RepairOrderPart) => {
    if (part) {
      setEditingPart(part);
      setPartForm({
        part: part.part,
        stock_item: part.stock_item,
        quantity: part.quantity,
        unit_cost: part.unit_cost,
        notes: part.notes,
      });
    } else {
      setEditingPart(null);
      setPartForm({
        part: null,
        stock_item: null,
        quantity: 1,
        unit_cost: 0,
        notes: '',
      });
    }
    setPartDialogOpen(true);
  };

  const handleSavePart = async () => {
    if (!order) return;
    try {
      if (editingPart) {
        await api.patch(
          `/api/order/repair-order/${order.pk}/parts/${editingPart.pk}/`,
          partForm
        );
      } else {
        await api.post(`/api/order/repair-order/${order.pk}/parts/`, partForm);
      }
      await fetchOrder();
      setPartDialogOpen(false);
      setSnackbar({
        open: true,
        message: `Part ${editingPart ? 'updated' : 'added'} successfully`,
        severity: 'success',
      });
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Failed to save part',
        severity: 'error',
      });
    }
  };

  const handleDeletePart = async (partPk: number) => {
    if (!order) return;
    try {
      await api.delete(`/api/order/repair-order/${order.pk}/parts/${partPk}/`);
      await fetchOrder();
      setSnackbar({
        open: true,
        message: 'Part removed successfully',
        severity: 'success',
      });
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: 'Failed to remove part',
        severity: 'error',
      });
    }
  };

  // Add/Edit labor
  const handleOpenLaborDialog = (labor?: RepairOrderLabor) => {
    if (labor) {
      setEditingLabor(labor);
      setLaborForm({
        description: labor.description,
        hours: labor.hours,
        rate: labor.rate,
        user: labor.user,
        date: labor.date,
      });
    } else {
      setEditingLabor(null);
      setLaborForm({
        description: '',
        hours: 1,
        rate: 0,
        user: null,
        date: new Date().toISOString().split('T')[0],
      });
    }
    setLaborDialogOpen(true);
  };

  const handleSaveLabor = async () => {
    if (!order) return;
    try {
      if (editingLabor) {
        await api.patch(
          `/api/order/repair-order/${order.pk}/labor/${editingLabor.pk}/`,
          laborForm
        );
      } else {
        await api.post(`/api/order/repair-order/${order.pk}/labor/`, laborForm);
      }
      await fetchOrder();
      setLaborDialogOpen(false);
      setSnackbar({
        open: true,
        message: `Labor entry ${editingLabor ? 'updated' : 'added'} successfully`,
        severity: 'success',
      });
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: err.response?.data?.detail || 'Failed to save labor entry',
        severity: 'error',
      });
    }
  };

  const handleDeleteLabor = async (laborPk: number) => {
    if (!order) return;
    try {
      await api.delete(`/api/order/repair-order/${order.pk}/labor/${laborPk}/`);
      await fetchOrder();
      setSnackbar({
        open: true,
        message: 'Labor entry removed successfully',
        severity: 'success',
      });
    } catch (err: any) {
      setSnackbar({
        open: true,
        message: 'Failed to remove labor entry',
        severity: 'error',
      });
    }
  };

  // Calculate totals
  const calculateTotalCost = (): number => {
    if (!order) return 0;
    const partsTotal = order.parts_used.reduce(
      (sum, part) => sum + (part.total_cost || part.quantity * part.unit_cost),
      0
    );
    const laborTotal = order.labor_entries.reduce(
      (sum, labor) => sum + (labor.total_cost || labor.hours * labor.rate),
      0
    );
    return partsTotal + laborTotal;
  };

  // Loading state
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={fetchOrder}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  // No order found
  if (!order) {
    return (
      <Box p={3}>
        <Alert severity="warning">
          Repair order not found. It may have been deleted or you may not have permission to view it.
        </Alert>
      </Box>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ flexGrow: 1, p: 3 }}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Repair Order: {order.reference || order.order_id}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <StatusRenderer status={order.status} statusText={order.status_text} />
              <Chip
                label={PRIORITY_OPTIONS.find(p => p.value === order.priority)?.label || 'Normal'}
                color={
                  order.priority >= 3 ? 'error' :
                  order.priority >= 2 ? 'warning' :
                  order.priority >= 1 ? 'info' : 'default'
                }
                size="small"
              />
              <Typography variant="body2" color="textSecondary">
                Created: {formatDate(order.creation_date)}
              </Typography>
            </Box>
          </Box>
          <Box display="flex" gap={1}>
            <Tooltip title="Refresh">
              <IconButton onClick={fetchOrder}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Print">
              <IconButton onClick={() => window.print()}>
                <PrintIcon />
              </IconButton>
            </Tooltip>
            {!editing ? (
              <Button
                variant="contained"
                startIcon={<EditIcon />}
                onClick={() => setEditing(true)}
                disabled={!user?.is_staff}
              >
                Edit
              </Button>
            ) : (
              <>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveOrder}
                  disabled={saving}
                >
                  {saving ? <CircularProgress size={24} /> : 'Save'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<CancelIcon />}
                  onClick={handleCancelEdit}
                  disabled={saving}
                >
                  Cancel
                </Button>
              </>
            )}
          </Box>
        </Box>

        {/* Main Content */}
        <Grid container spacing={3}>
          {/* Order Details Card */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Order Details
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    {editing ? (
                      <TextField
                        fullWidth
                        label="Description"
                        multiline
                        rows={3}
                        value={editForm.description || ''}
                        onChange={(e) =>
                          setEditForm({ ...editForm, description: e.target.value })
                        }
                      />
                    ) : (
                      <Box>
                        <Typography variant="subtitle2" color="textSecondary">
                          Description
                        </Typography>
                        <Typography variant="body1">
                          {order.description || 'No description provided'}
                        </Typography>
                      </Box>
                    )}
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    {editing ? (
                      <FormControl fullWidth>
                        <InputLabel>Status</InputLabel>
                        <Select
                          value={editForm.status || order.status}
                          label="Status"
                          onChange={(e) =>
                            setEditForm({ ...editForm, status: e.target.value as number })
                          }
                        >
                          {REPAIR_ORDER_STATUSES.map((status) => (
                            <MenuItem key={status.value} value={status.value}>
                              {status.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    ) : (
                      <Box>
                        <