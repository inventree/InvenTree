import { Text } from "@mantine/core";
import { useQuery } from '@tanstack/react-query';

export function fetchTodos() {
    return fetch('https://jsonplaceholder.typicode.com/todos/1').then((res) => res.json())
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
