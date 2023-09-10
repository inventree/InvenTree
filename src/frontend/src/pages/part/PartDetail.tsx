import { Text } from '@mantine/core';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../../App';

export default function PartDetail() {
  const { id } = useParams();

  return (
    <>
      <h1>Part Detail</h1>
      <Text>ID: {id}</Text>
    </>
  );
}
