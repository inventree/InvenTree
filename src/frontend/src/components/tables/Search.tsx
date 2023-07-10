import { TextInput } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';


export function TableSearchInput({
    searchCallback
} : {
    searchCallback: (searchTerm: string) => void;
}) {

    // Debounce timer
    let timer: any = null;

    function handleSearch(event: any) {
        const value = event.target.value;

        clearTimeout(timer);

        timer = setTimeout(() => {
            searchCallback(value);
        }, 250);
    }

    return <TextInput
        icon={<IconSearch />}
        placeholder="Search"
        onChange={handleSearch}
        />;
}