import { Box, Image, Skeleton } from '@mantine/core';
import QR from 'qrcode';
import { useEffect, useState } from 'react';

export type QRCodeProps = {
  ecl?: 'L' | 'M' | 'Q' | 'H';
  margin?: number;
  data?: string;
};

/**
 * Render a QR code with the provided data.
 */
export const QRCode = ({ data, ecl = 'Q', margin = 1 }: QRCodeProps) => {
  const [qrCode, setQRCode] = useState<string>();

  useEffect(() => {
    if (!data) return setQRCode(undefined);

    QR.toString(data, { errorCorrectionLevel: ecl, type: 'svg', margin }).then(
      (svg) => {
        setQRCode(`data:image/svg+xml;utf8,${encodeURIComponent(svg)}`);
      }
    );
  }, [data, ecl]);

  return (
    <Box>
      {qrCode ? (
        <Image src={qrCode} alt='QR Code' />
      ) : (
        <Skeleton height={500} />
      )}
    </Box>
  );
};
