import { Trans, t } from '@lingui/macro';
import {
  Box,
  Code,
  Group,
  Image,
  Select,
  Skeleton,
  Stack,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import QR from 'qrcode';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { CopyButton } from '../buttons/CopyButton';

type QRCodeProps = {
  ecl?: 'L' | 'M' | 'Q' | 'H';
  margin?: number;
  data?: string;
};

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
        <Image src={qrCode} alt="QR Code" />
      ) : (
        <Skeleton height={500} />
      )}
    </Box>
  );
};

type InvenTreeQRCodeProps = {
  model: ModelType;
  pk: number;
  showEclSelector?: boolean;
} & Omit<QRCodeProps, 'data'>;

export const InvenTreeQRCode = ({
  showEclSelector = true,
  model,
  pk,
  ecl: eclProp = 'Q',
  ...props
}: InvenTreeQRCodeProps) => {
  const settings = useGlobalSettingsState();
  const [ecl, setEcl] = useState(eclProp);

  useEffect(() => {
    if (eclProp) setEcl(eclProp);
  }, [eclProp]);

  const { data } = useQuery({
    queryKey: ['qr-code', model, pk],
    queryFn: async () => {
      const res = await api.post(apiUrl(ApiEndpoints.generate_barcode), {
        model,
        pk
      });

      return res.data?.barcode as string;
    }
  });

  const eclOptions = useMemo(
    () => [
      { value: 'L', label: t`Low (7%)` },
      { value: 'M', label: t`Medium (15%)` },
      { value: 'Q', label: t`Quartile (25%)` },
      { value: 'H', label: t`High (30%)` }
    ],
    []
  );

  return (
    <Stack>
      <QRCode data={data} ecl={ecl} {...props} />

      {data && settings.getSetting('BARCODE_SHOW_TEXT', 'false') && (
        <Group
          justify={showEclSelector ? 'space-between' : 'center'}
          align="flex-start"
          px={16}
        >
          <Stack gap={4} pt={2}>
            <Text size="sm" fw={500}>
              <Trans>Barcode Data:</Trans>
            </Text>
            <Group>
              <Code>{data}</Code>
              <CopyButton value={data} />
            </Group>
          </Stack>

          {showEclSelector && (
            <Select
              allowDeselect={false}
              label={t`Select Error Correction Level`}
              value={ecl}
              onChange={(v) =>
                setEcl(v as Exclude<QRCodeProps['ecl'], undefined>)
              }
              data={eclOptions}
            />
          )}
        </Group>
      )}
    </Stack>
  );
};
