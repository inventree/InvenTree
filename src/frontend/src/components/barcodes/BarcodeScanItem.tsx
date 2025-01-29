import type { ModelType } from '../../enums/ModelType';

/**
 * Interface defining a single barcode scan item
 * @param id: Unique identifier for the scan
 * @param barcode: Scanned barcode data
 * @param data: Data returned from the server
 * @param instance: Instance of the scanned item (if discovered)
 * @param timestamp: Date and time of the scan
 * @param source: Source of the scan (e.g. 'barcode', 'QR code')
 * @param model: Model type of the scanned item
 * @param pk: Primary key of the scanned item
 */
export interface BarcodeScanItem {
  id: string;
  barcode: string;
  data?: any;
  instance?: any;
  timestamp: Date;
  source: string;
  model?: ModelType;
  pk?: string;
}
