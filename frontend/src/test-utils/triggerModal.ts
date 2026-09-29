import { act } from "@testing-library/react";

import type { mockModal } from "./mocks/modal";

type ModalSpy = typeof mockModal;

/**
 * Invokes the last-rendered Modal's `onSubmit` inside `act` and awaits any promise
 * chain the source wires (e.g. `.then(() => onSuccess?.())`). Use this whenever the
 * modal's submit flow needs a full flush before assertions.
 */
export async function triggerModalSubmit(modalSpy: ModalSpy) {
  await act(async () => {
    await modalSpy.mock.lastCall![0].onSubmit();
  });
}

/**
 * Invokes the last-rendered Modal's `onCancel` inside `act`. `onCancel` is typed
 * as optional on the Modal contract but every wired usage passes one — the
 * optional-chain here documents "we expect this to be present" and stays honest
 * if the source ever stops wiring it.
 */
export function triggerModalCancel(modalSpy: ModalSpy) {
  act(() => modalSpy.mock.lastCall![0].onCancel?.());
}
