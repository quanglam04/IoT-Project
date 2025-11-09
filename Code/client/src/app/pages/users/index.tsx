import { users } from './dummy'

const UserPage = () => {
  return (
    <div className='rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 p-6'>
      <div className='rounded-3xl border-2 border-gray-800 bg-white p-8 shadow-lg'>
        <h2 className='mb-8 text-3xl font-bold'>Users (Admin)</h2>

        <div className='overflow-x-auto'>
          <table className='w-full'>
            <thead>
              <tr className='border-b-2 border-gray-300'>
                <th className='px-6 py-4 text-left text-lg font-bold'>Email</th>
                <th className='px-6 py-4 text-left text-lg font-bold'>Role</th>
                <th className='px-6 py-4 text-left text-lg font-bold'>Status</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user, index) => (
                <tr key={index} className='border-b border-gray-200'>
                  <td className='px-6 py-4'>{user.email}</td>
                  <td className='px-6 py-4'>{user.role}</td>
                  <td className='px-6 py-4'>{user.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default UserPage
