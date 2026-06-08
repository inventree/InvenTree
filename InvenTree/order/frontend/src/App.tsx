import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { PageLayout } from '../components/nav/PageLayout';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

// Lazy-loaded repair order page components
const RepairOrderList = lazy(() => import('../pages/repair/RepairOrderList'));
const RepairOrderDetail = lazy(() => import('../pages/repair/RepairOrderDetail'));
const RepairOrderCreate = lazy(() => import('../pages/repair/RepairOrderCreate'));

/**
 * Main application router component.
 * Provides routes for the Repair Order feature:
 * - /repair/          -> List all repair orders
 * - /repair/new/      -> Create a new repair order
 * - /repair/:id/      -> View/edit a specific repair order
 * - /repair/:id/*     -> Nested routes within a repair order detail
 *
 * All repair routes are wrapped in a PageLayout for consistent navigation
 * and are lazy-loaded with Suspense fallback.
 */
const App: React.FC = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        {/* Redirect root to repair list */}
        <Route path="/" element={<Navigate to="/repair/" replace />} />

        {/* Repair order routes */}
        <Route
          path="/repair/*"
          element={
            <PageLayout title="Repair Orders">
              <Suspense fallback={<LoadingSpinner />}>
                <RepairOrderRoutes />
              </Suspense>
            </PageLayout>
          }
        />

        {/* Catch-all: redirect unknown routes to repair list */}
        <Route path="*" element={<Navigate to="/repair/" replace />} />
      </Routes>
    </Suspense>
  );
};

/**
 * Nested routes for repair order pages.
 * Separated to allow proper relative routing within the /repair/ base path.
 */
const RepairOrderRoutes: React.FC = () => {
  return (
    <Routes>
      {/* List all repair orders */}
      <Route index element={<RepairOrderList />} />

      {/* Create a new repair order */}
      <Route path="new/" element={<RepairOrderCreate />} />

      {/* View/edit a specific repair order by ID */}
      <Route path=":id/" element={<RepairOrderDetail />} />

      {/* Nested routes within a repair order (e.g., line items, history) */}
      <Route path=":id/*" element={<RepairOrderDetail />} />

      {/* Redirect unknown sub-routes to the repair list */}
      <Route path="*" element={<Navigate to="/repair/" replace />} />
    </Routes>
  );
};

export default App;