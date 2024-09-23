import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';

export default function PartSchedulingDetail({ partId }: { partId: number }) {
  const user = useUserState();
  const table = useTable('part-scheduling');

  return (
    <>
      <div>Hello world</div>
    </>
  );
}
