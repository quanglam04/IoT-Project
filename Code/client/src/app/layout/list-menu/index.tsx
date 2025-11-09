import { useNavigate, useLocation } from 'react-router-dom'
import { listMenu } from './list-menu'

const ListMenu = () => {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className='flex flex-col space-y-2'>
      {listMenu.map((menu, index) => {
        const isActive = location.pathname === menu.navigateTo

        return (
          <div
            key={index}
            onClick={() => {
              navigate(menu.navigateTo)
            }}
            className={`cursor-pointer rounded-lg px-4 py-3 font-bold transition-colors ${
              isActive ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'
            } `}
          >
            {menu.title}
          </div>
        )
      })}
    </div>
  )
}

export default ListMenu
