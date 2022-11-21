import { useQuery } from '@tanstack/react-query';
import { api } from '../App';
import { StatisticItem } from './items/DashboardItem';
import { useEffect, useState } from 'react';

export function DashboardItemProxy({
  id,
  text,
  url,
  params,
  autoupdate = true
}: {
  id: string;
  text: string;
  url: string;
  params: any;
  autoupdate: boolean;
}) {
  function fetchData() {
    return api
      .get(`${url}/?search=&offset=0&limit=25`, { params: params })
      .then((res) => res.data);
  }
  const { isLoading, error, data, isFetching } = useQuery({
    queryKey: [`dash_${id}`],
    queryFn: fetchData,
    refetchOnWindowFocus: autoupdate
  });
  const [dashdata, setDashData] = useState({ title: 'Title', value: '000' });

  useEffect(() => {
    if (data) {
      setDashData({ title: text, value: data.count });
    }
  }, [data]);

  if (error) return <>An error has occurred: {error}</>;
  return (
    <div key={id}>
      <StatisticItem
        id={id}
        data={dashdata}
        isLoading={isLoading || isFetching}
      />
    </div>
  );
}
