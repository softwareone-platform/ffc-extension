import {
  buildRqlQuery,
  GridDefaultConfiguration,
} from "@swo/design-system/grid";
import {
  DefaultError,
  keepPreviousData,
  QueryKey,
  useQuery,
  useQueryClient,
  UseQueryOptions,
} from "@tanstack/react-query";
import { RqlQuery } from "@swo/rql-client";
import { useCallback, useMemo, useRef, useState } from "react";

interface StateRef<TEntity extends object, TOptions> {
  options: TOptions;
  query: RqlQuery<TEntity>;
  isInitialised: boolean;
  baseQueryKey: QueryKey;
}
/**
 *
 * @param baseQueryKey Query key to be invalidated when doing a refresh or silent refresh
 * @param options Function to generate the query options. Takes the current RqlQuery as a parameter
 * @param pagingOption Enable or disable paging. If disabled, the total will be set to undefined
 * @returns
 */
export function useReactQueryRqlGrid<
  TEntity extends object,
  TQueryFnData = unknown,
  TError = DefaultError,
  TQueryKey extends QueryKey = QueryKey,
>(
  baseQueryKey: TQueryKey,
  options: (
    query: RqlQuery<TEntity>,
  ) => UseQueryOptions<
    TQueryFnData,
    TError,
    { data: TEntity[]; total?: number },
    TQueryKey
  >,
  pagingOption: "DisablePaging" | "EnablePaging" = "EnablePaging",
) {
  const queryClient = useQueryClient();

  const [query, setQuery] = useState(new RqlQuery<TEntity>());
  const [isInitialised, setIsInitialised] = useState(false);
  const [isSilentRefresh, setIsSilentRefresh] = useState(false);
  const stateRef = useRef<StateRef<TEntity, ReturnType<typeof options>>>({
    query,
    options: {} as ReturnType<typeof options>,
    baseQueryKey,
    isInitialised,
  });
  stateRef.current = {
    query,
    isInitialised,
    options: options(query.clone()),
    baseQueryKey,
  };

  const { data, isFetching, error } = useQuery({
    ...stateRef.current.options,
    // placeholderData: keepPreviousData,
    enabled: isInitialised,
  });

  const onConfigChange = useCallback(
    async (config: GridDefaultConfiguration<TEntity>) => {
      const { isInitialised, query: oldQuery } = stateRef.current;
      if (!isInitialised) {
        setIsInitialised(true);
      }
      const newQuery = buildRqlQuery<TEntity>(config);
      if (oldQuery.toString() === newQuery.toString()) {
        return;
      }
      setQuery(newQuery);
      setIsSilentRefresh(false);
    },
    [],
  );

  const abort = useCallback(() => {
    const queryKey = stateRef.current.options.queryKey;
    queryClient.cancelQueries({ queryKey });
  }, [queryClient]);

  const refresh = useCallback(async () => {
    console.log("Refreshing data...", stateRef.current);
    setIsSilentRefresh(false);
    console.log("Invalidating queries with key:", stateRef.current.baseQueryKey);
    console.log(queryClient.getQueryCache().getAll());
    queryClient.invalidateQueries({ queryKey: stateRef.current.options.queryKey });
  }, [queryClient]);

  const silentRefresh = useCallback(async () => {
    console.log("Silent Refreshing data...", stateRef.current);
    setIsSilentRefresh(true);
    queryClient.invalidateQueries({ queryKey: stateRef.current.baseQueryKey });
  }, [queryClient]);

  return useMemo(
    () => ({
      ...(data
        ? data
        : {
            total: pagingOption === "DisablePaging" ? undefined : 0,
            data: [],
          }),
      isLoading: isFetching && !isSilentRefresh,
      refresh,
      onConfigChange,
      abort,
      silentRefresh,
      error,
    }),
    [
      abort,
      data,
      error,
      isFetching,
      isSilentRefresh,
      pagingOption,
      onConfigChange,
      refresh,
      silentRefresh,
    ],
  );
}
