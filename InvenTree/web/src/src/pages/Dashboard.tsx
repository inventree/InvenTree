import { Text } from "@mantine/core";
import { useQuery } from '@tanstack/react-query';
import api from "../api";

export function fetchTodos() {
    return api.get('/todos/1').then((res) => res.data);
}

export function Dashboard() {
    const { isLoading, error, data, isFetching } = useQuery({ queryKey: ['todos'], queryFn: fetchTodos });

    if (isLoading)
        return <>Loading...</>;
    if (error)
        return <>An error has occurred: {error.message}</>;
    return (<>
        <Text>Dashboard</Text>
        <div>{isFetching ? "Updating..." : ""}</div>
        <div>{data.title}</div>
    </>);
}
