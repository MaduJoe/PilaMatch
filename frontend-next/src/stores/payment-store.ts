import { create } from 'zustand';

interface PaymentState {
  orderId: string | null;
  amount: number | null;
  orderName: string | null;
  customerName: string | null;
  contractId: string | null;
  subscriptionId: string | null;
  clientKey: string | null;
  isProcessing: boolean;

  setPaymentData: (data: {
    orderId: string;
    amount: number;
    orderName: string;
    customerName?: string | null;
    contractId?: string | null;
    subscriptionId?: string | null;
    clientKey?: string | null;
  }) => void;

  setProcessing: (processing: boolean) => void;
  reset: () => void;
}

export const usePaymentStore = create<PaymentState>((set) => ({
  orderId: null,
  amount: null,
  orderName: null,
  customerName: null,
  contractId: null,
  subscriptionId: null,
  clientKey: null,
  isProcessing: false,

  setPaymentData: (data) =>
    set({
      orderId: data.orderId,
      amount: data.amount,
      orderName: data.orderName,
      customerName: data.customerName ?? null,
      contractId: data.contractId ?? null,
      subscriptionId: data.subscriptionId ?? null,
      clientKey: data.clientKey ?? null,
      isProcessing: false,
    }),

  setProcessing: (isProcessing) => set({ isProcessing }),

  reset: () =>
    set({
      orderId: null,
      amount: null,
      orderName: null,
      customerName: null,
      contractId: null,
      subscriptionId: null,
      clientKey: null,
      isProcessing: false,
    }),
}));
