import { Trans, t } from '@lingui/macro';
import {
  Alert,
  Box,
  Button,
  Code,
  Group,
  Image,
  Select,
  Skeleton,
  Stack,
  Text
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { modals } from '@mantine/modals';
import { useQuery } from '@tanstack/react-query';
import QR from 'qrcode';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { CopyButton } from '../buttons/CopyButton';
import { QrCodeType } from './ActionDropdown';
import { BarcodeInput } from './BarcodeInput';

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
  mdl_prop: QrCodeType;
  showEclSelector?: boolean;
} & Omit<QRCodeProps, 'data'>;

export const InvenTreeQRCode = ({
  mdl_prop,
  showEclSelector = true,
  ecl: eclProp = 'Q',
  ...props
}: InvenTreeQRCodeProps) => {
  const settings = useGlobalSettingsState();
  const [ecl, setEcl] = useState(eclProp);

  useEffect(() => {
    if (eclProp) setEcl(eclProp);
  }, [eclProp]);

  const { data } = useQuery({
    queryKey: ['qr-code', mdl_prop.model, mdl_prop.pk],
    queryFn: async () => {
      const res = await api.post(apiUrl(ApiEndpoints.generate_barcode), {
        model: mdl_prop.model,
        pk: mdl_prop.pk
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
      {mdl_prop.hash ? (
        <Alert variant="outline" color="red" title={t`Custom barcode`}>
          <Trans>
            A custom barcode is registered for this item. The shown code is not
            that custom barcode.
          </Trans>
        </Alert>
      ) : null}

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

export const QRCodeLink = ({ mdl_prop }: { mdl_prop: QrCodeType }) => {
  const [barcode, setBarcode] = useState('');
  const [isScanning, toggleIsScanning] = useDisclosure(false);

  function linkBarcode(value?: string) {
    api
      .post(apiUrl(ApiEndpoints.barcode_link), {
        [mdl_prop.model]: mdl_prop.pk,
        barcode: value || barcode
      })
      .then((response) => {
        modals.closeAll();
        location.reload();
      });
  }
  const actionSubmit = (decodedText: string) => {
    linkBarcode(decodedText);
  };

  const handleLinkBarcode = () => {
    linkBarcode(barcode);
  };

  return (
    <BarcodeInput
      value={barcode}
      onChange={(event) => setBarcode(event.currentTarget.value)}
      onScan={actionSubmit}
      onAction={handleLinkBarcode}
      actionText={t`Link`}
    />
  );
};

export const QRCodeUnlink = ({ mdl_prop }: { mdl_prop: QrCodeType }) => {
  function unlinkBarcode() {
    api
      .post(apiUrl(ApiEndpoints.barcode_unlink), {
        [mdl_prop.model]: mdl_prop.pk
      })
      .then((response) => {
        modals.closeAll();
        location.reload();
      });
  }
  return (
    <Box>
      <Text>
        <Trans>This will remove the link to the associated barcode</Trans>
      </Text>
      <Button color="red" onClick={unlinkBarcode}>
        <Trans>Unlink Barcode</Trans>
      </Button>
    </Box>
  );
};
