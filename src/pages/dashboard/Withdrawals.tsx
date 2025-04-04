import React from 'react'

const Withdrawals = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-gray-900">Withdrawals</h1>
            <p className="mt-1 text-sm text-gray-600">Withdraw your earnings to M-Pesa</p>
          </div>

          {/* Balance Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg mb-8">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900">Available Balance</h2>
              <div className="mt-2 flex items-baseline">
                <p className="text-3xl font-semibold text-gray-900">KES 0.00</p>
                <p className="ml-2 text-sm text-gray-500">available for withdrawal</p>
              </div>
            </div>
          </div>

          {/* Withdrawal Form */}
          <div className="bg-white shadow sm:rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Make a Withdrawal</h3>
              <div className="mt-2 max-w-xl text-sm text-gray-500">
                <p>Withdraw your earnings directly to your M-Pesa account.</p>
              </div>
              <form className="mt-5">
                <div className="grid grid-cols-6 gap-6">
                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
                      Amount (KES)
                    </label>
                    <input
                      type="number"
                      name="amount"
                      id="amount"
                      min="10"
                      step="1"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      placeholder="Enter amount"
                    />
                  </div>

                  <div className="col-span-6 sm:col-span-3">
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                      M-Pesa Phone Number
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      id="phone"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      placeholder="254700000000"
                    />
                  </div>
                </div>

                <div className="mt-6">
                  <button
                    type="submit"
                    className="w-full sm:w-auto inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                  >
                    Withdraw to M-Pesa
                  </button>
                </div>
              </form>
            </div>
          </div>

          {/* Withdrawal History */}
          <div className="mt-8">
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h2 className="text-lg leading-6 font-medium text-gray-900">Withdrawal History</h2>
                <p className="mt-1 text-sm text-gray-500">Your recent withdrawals will appear here</p>
              </div>
              <div className="border-t border-gray-200">
                <div className="bg-gray-50 px-4 py-5 sm:p-6">
                  <p className="text-center text-gray-500">No withdrawals made yet</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Withdrawals 