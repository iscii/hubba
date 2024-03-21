import { Outlet } from 'react-router-dom';
import { AuthRoutes } from '@/features/auth';
import { Interface } from '@/components/layout';
import { Home } from '@/pages/Home';
import { NotFound } from '@/pages/NotFound';

const App = () => {
    return <Outlet />;
};

export const publicRoutes = [
    {
        path: '/',
        element: <App />,
        children: [
            {
                path: '/',
                element: (
                    <Interface>
                        <Home />
                    </Interface>
                ),
            },
            { path: '/auth/*', element: <AuthRoutes /> },
            // 404
            { path: '*', element: <NotFound /> },
        ],
    },
];
