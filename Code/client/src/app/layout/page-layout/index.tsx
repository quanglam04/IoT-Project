import { Outlet } from 'react-router-dom'
import Header from '../header'
import ListMenu from '../list-menu'

const PageLayoutPage = () => {
  return (
    <div className='flex min-h-screen bg-gray-50'>
      <div className='w-56 border-r border-gray-200 bg-white p-4'>
        <ListMenu />
      </div>

      <div className='flex flex-1 flex-col'>
        <div className='flex justify-end p-4'>
          <Header />
        </div>

        <div className='flex-1 p-6'>
          <Outlet />
        </div>
      </div>
    </div>
  )
}

export default PageLayoutPage
