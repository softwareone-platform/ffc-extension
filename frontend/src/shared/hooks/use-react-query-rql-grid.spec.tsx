// import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query';
// import { renderHook, waitFor } from '@testing-library/react';
// import { PropsWithChildren, act } from 'react';

// import { GridDefaultConfiguration, buildRqlQuery } from '@swo/design-system/grid';
// import { RqlQuery } from '@swo/rql-client';

// import { useReactQueryRqlGrid } from './useReactQueryRqlGrid';

// jest.mock('@swo/grid', () => ({
//   ...jest.requireActual('@swo/grid'),
//   buildRqlQuery: jest.fn(),
// }));

// function createWrapper() {
//   const queryClient = new QueryClient({
//     defaultOptions: {
//       queries: {
//         retry: false,
//       },
//     },
//   });

//   function TestComponent({ children }: PropsWithChildren) {
//     return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
//   }

//   return TestComponent;
// }

// describe('useReactQueryRqlGrid', () => {
//   const mockData = {
//     data: [
//       { id: '1', name: 'Test Entity' },
//       { id: '2', name: 'Another Entity' },
//     ],
//     total: 2,
//   };

//   const mockQueryFn = jest.fn().mockResolvedValue(mockData);
//   const mockBaseQueryKey = ['test-entities'];
//   const mockBuildRqlQuery = buildRqlQuery as jest.MockedFunction<typeof buildRqlQuery<{ name: string }>>;

//   beforeEach(() => {
//     jest.clearAllMocks();
//     mockBuildRqlQuery.mockImplementation(() => new RqlQuery());
//   });

//   it('should initialize with empty data array and total 0', () => {
//     const options = (query: RqlQuery<object>) => ({
//       queryKey: ['test-entities', query.toString()],
//       queryFn: mockQueryFn,
//     });

//     const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), { wrapper: createWrapper() });

//     expect(result.current.data).toEqual([]);
//     expect(result.current.total).toBe(0);
//     expect(result.current.isLoading).toBe(false);
//   });

//   it('should not execute query until onConfigChange is called', () => {
//     const options = (query: RqlQuery<object>) => ({
//       queryKey: ['test-entities', query.toString()],
//       queryFn: mockQueryFn,
//     });

//     renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), { wrapper: createWrapper() });

//     expect(mockQueryFn).not.toHaveBeenCalled();
//   });

//   it('should execute query after onConfigChange is called', async () => {
//     const options = (query: RqlQuery<object>) => ({
//       queryKey: ['test-entities', query.toString()],
//       queryFn: mockQueryFn,
//     });

//     const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), { wrapper: createWrapper() });

//     const mockConfig: Partial<GridDefaultConfiguration<object>> = {
//       sort: [{ field: 'name', direction: 'asc' }],
//     };

//     await act(() => result.current.onConfigChange(mockConfig as GridDefaultConfiguration<object>));

//     await waitFor(() => {
//       expect(mockBuildRqlQuery).toHaveBeenCalledWith(mockConfig);
//       expect(mockQueryFn).toHaveBeenCalledTimes(1);
//     });
//   });

//   it('should not execute new query if the RQL query string does not change', async () => {
//     mockBuildRqlQuery.mockImplementation(() => {
//       const query = new RqlQuery<{ name: string }>();
//       query.toString = jest.fn().mockReturnValue('sort(+name)');
//       return query;
//     });

//     const options = jest.fn((query: RqlQuery<object>) => ({
//       queryKey: ['test-entities', query.toString()],
//       queryFn: mockQueryFn,
//     }));

//     const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options), { wrapper: createWrapper() });

//     const mockConfig = { sort: [{ field: 'name', direction: 'asc' }] } as GridDefaultConfiguration<object>;
//     mockBuildRqlQuery.mockImplementation(() => new RqlQuery<{ name: string }>().orderBy(['name', 'asc']));
//     await act(() => result.current.onConfigChange(mockConfig));

//     await waitFor(() => {
//       expect(options.mock.lastCall?.[0].toString()).toBe('order=name');
//     });

//     mockQueryFn.mockClear();

//     mockBuildRqlQuery.mockImplementation(() => new RqlQuery<{ name: string }>().orderBy(['name', 'asc']));
//     await act(() => result.current.onConfigChange(mockConfig as GridDefaultConfiguration<object>));

//     expect(options.mock.lastCall?.[0].toString()).toBe('order=name');
//   });

//   it('should invalidate queries when refresh is called', async () => {
//     const wrapper = createWrapper();

//     const { result } = renderHook(
//       () => {
//         const queryClient = useQueryClient();
//         const grid = useReactQueryRqlGrid(mockBaseQueryKey, (query: RqlQuery<object>) => ({
//           queryKey: [...mockBaseQueryKey, query.toString()],
//           queryFn: mockQueryFn,
//         }));
//         return { grid, queryClient };
//       },
//       { wrapper }
//     );

//     const invalidateQueriesSpy = jest.spyOn(result.current.queryClient, 'invalidateQueries');

//     await act(() => result.current.grid.refresh());

//     expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: mockBaseQueryKey });
//   });

//   it('should invalidate queries when silentRefresh is called without showing loading state', async () => {
//     const wrapper = createWrapper();

//     const { result } = renderHook(
//       () => {
//         const queryClient = useQueryClient();
//         const grid = useReactQueryRqlGrid(mockBaseQueryKey, (query: RqlQuery<object>) => ({
//           queryKey: [...mockBaseQueryKey, query.toString()],
//           queryFn: mockQueryFn,
//         }));
//         return { grid, queryClient };
//       },
//       { wrapper }
//     );

//     const invalidateQueriesSpy = jest.spyOn(result.current.queryClient, 'invalidateQueries');

//     await act(() => result.current.grid.silentRefresh());

//     expect(invalidateQueriesSpy).toHaveBeenCalledWith({ queryKey: mockBaseQueryKey });
//   });

//   it('should cancel queries when abort is called', async () => {
//     const wrapper = createWrapper();

//     const { result } = renderHook(
//       () => {
//         const queryClient = useQueryClient();
//         const grid = useReactQueryRqlGrid(mockBaseQueryKey, (query: RqlQuery<object>) => ({
//           queryKey: [...mockBaseQueryKey, query.toString()],
//           queryFn: mockQueryFn,
//         }));
//         return { grid, queryClient };
//       },
//       { wrapper }
//     );

//     await act(() =>
//       result.current.grid.onConfigChange({ sort: [{ field: 'name', direction: 'asc' }] } as GridDefaultConfiguration<object>)
//     );

//     const cancelQueriesSpy = jest.spyOn(result.current.queryClient, 'cancelQueries');

//     await act(() => result.current.grid.abort());

//     await waitFor(() => {
//       expect(cancelQueriesSpy).toHaveBeenCalled();
//     });
//   });

//   it('should set total to undefined when DisablePaging option is provided', () => {
//     const options = (query: RqlQuery<object>) => ({
//       queryKey: ['test-entities', query.toString()],
//       queryFn: mockQueryFn,
//     });

//     const { result } = renderHook(() => useReactQueryRqlGrid(mockBaseQueryKey, options, 'DisablePaging'), { wrapper: createWrapper() });

//     expect(result.current.total).toBeUndefined();
//   });
// });
